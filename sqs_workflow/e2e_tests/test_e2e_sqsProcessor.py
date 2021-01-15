import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest import TestCase
import concurrent.futures

import boto3
import requests

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor


class E2ETestSqsProcessor(TestCase):
    similarity_processor = SimilarityProcessor()
    processor = SqsProcessor("-immoviewer-ai")
    s3_helper = S3Helper()

    def pull_messages(self, processor: SqsProcessor, number_of_messages: int) -> list:
        attemps = 0
        list_of_messages = processor.receive_messages_from_queue(number_of_messages)
        while attemps < 7 and len(list_of_messages) < number_of_messages:
            messages_received = processor.receive_messages_from_queue(1)
            if len(messages_received) > 0:
                list_of_messages += messages_received
                print('len list of messages = ', len(list_of_messages))
            else:
                attemps += 1
                time.sleep(1)
            print('attemps =', attemps)
        if attemps == 3:
            logging.info('out of attemps')
        return list_of_messages

    def clear_directory(self, path_to_folder_in_bucket: str):
        sync_command = f"aws s3 --profile {os.environ['AWS_PROFILE']} rm s3://{os.environ['S3_BUCKET']}/{path_to_folder_in_bucket} --recursive"
        logging.info(f'sync command: {sync_command}')
        stream = os.popen(sync_command)
        output = stream.read()
        logging.info(f'output: {output}')

    def purge_queue(self, queue_url):
        sqs_client = boto3.client('sqs', region_name='eu-central-1')
        req_purge = sqs_client.purge_queue(QueueUrl=queue_url)
        logging.info(f'Queue is purged')
        return req_purge

    def pull_messages_return_queue(self, max_num_of_messages):
        # pulled_message = self.processor.pull_messages(1)
        logging.info('Pulled message')
        attempts = 0
        list_of_messages = self.processor.sqs_client.receive_message(QueueUrl=self.processor.return_queue_url,
                                                                     MaxNumberOfMessages=max_num_of_messages,
                                                                     MessageAttributeNames=['All'])
        while attempts < 7 and len(list_of_messages) < max_num_of_messages:
            messages_received = self.processor.sqs_client.receive_message(QueueUrl=self.processor.return_queue_url,
                                                                          MaxNumberOfMessages=1,
                                                                          MessageAttributeNames=['All'])
            if len(messages_received) > 0:
                list_of_messages += messages_received
                logging.info(f'Len list of messages:{len(list_of_messages)}')
            else:
                attempts += 1
                time.sleep(2)
            logging.info(f'attempts:{attempts} left')
        if attempts == 7:
            logging.info(f'Out of attempts')
        return list_of_messages

    def test_load_e2e(self):
        bucket = "immoviewer-ai-test"
        prefix = "storage/segmentation/"
        self.s3_helper.s3_bucket = bucket
        list_of_files = self.s3_helper.list_s3_objects(prefix)
        list_of_files = list_of_files[:300]
        inference_id = "e2e-inference/"
        message_index = 0
        messages = []
        for s3_file in list_of_files:
            document_url = f'https://{bucket}.s3-eu-west-1.amazonaws.com/{s3_file}'
            message_index = message_index + 1
            preprocessing_message = {
                StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
                "orderId": "5da5d5164cedfd0050363a2e",
                "floor": 1,
                "tourId": "1342386",
                StringConstants.INFERENCE_ID_KEY: f"{inference_id}{str(message_index)}",
                StringConstants.DOCUMENT_PATH_KEY: document_url,
                StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value,
                                            ProcessingTypesEnum.ObjectsDetecting.value]
            }
            messages.append(preprocessing_message)
        executor = ThreadPoolExecutor(5)
        self.processor.queue_url = 'https://eu-central-1.queue.amazonaws.com/700659137911/staging-immoviewer-ai'
        messages_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(self.processor.send_message_to_queue, json.dumps(message),
                                             self.processor.queue_url): message for message in messages}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    messages_results.append(data)
                except Exception as exc:
                    logging.error('%r generated an exception: %s' % (url, exc))
                else:
                    logging.info('%r page is %d bytes' % (url, len(data)))
        print(messages_results)
        self.assertTrue(len(messages_results) > 0)



    def test_e2e(self):
        # E2EUtils.purge_queue(self.processor.queue_url)
        # E2EUtils.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')
        document_url = "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/similarity/test_w_5_panos_without_layout.json"
        document_object = requests.get(document_url).json()

        inference_id = f'e2e-test-{datetime.now()}'.replace(' ', '').replace(':', '')
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
            "orderId": "5da5d5164cedfd0050363a2e",
            "floor": 1,
            "tourId": "1342386",
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.DOCUMENT_PATH_KEY: document_url,
            StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value,
                                        ProcessingTypesEnum.ObjectsDetecting.value]
        }
        # Sends message to queue
        send_preprocessing_message_result = self.processor.send_message_to_queue(
            json.dumps(preprocessing_message),
            self.processor.queue_url)
        logging.info(f'Preprocessing_message:{send_preprocessing_message_result["MessageId"]} sent to queue')

        # Sleep 5 min
        time.sleep(65)  # 300 sec
        print('AFTER SLEEP')
        number_of_processed_steps_results = 0
        # todo check on s3 while all is ready
        expected_number_of_results = len(preprocessing_message[StringConstants.STEPS_KEY]) * len(
            document_object[StringConstants.PANOS_KEY])
        while number_of_processed_steps_results < expected_number_of_results:
            time.sleep(60)
            number_of_processed_steps_results = 0
            for step in preprocessing_message[StringConstants.STEPS_KEY]:
                s3_step_results = self.s3_helper.list_s3_objects(os.path.join(StringConstants.COMMON_PREFIX,
                                                                              step,
                                                                              inference_id))
                number_of_processed_steps_results = number_of_processed_steps_results + len(s3_step_results)
            logging.info(f"Found {number_of_processed_steps_results} results so far")
        logging.info("All steps are processed. Now waiting till similarity finishes.")

        # todo check that similarity message is returned
        resp_return = self.processor.sqs_client.get_queue_attributes(QueueUrl=self.processor.queue_url,
                                                                     AttributeNames=['All'])
        similarity_step_results = self.s3_helper.list_s3_objects(os.path.join(StringConstants.COMMON_PREFIX,
                                                                              ProcessingTypesEnum.Similarity.value,
                                                                              inference_id))

        s3_key = os.path.join(StringConstants.COMMON_PREFIX, ProcessingTypesEnum.Similarity.value, inference_id,
                              'similarity', StringConstants.RESULT_FILE_NAME)

        path_to_download = os.path.join(str(Path.home()), 'projects', 'python', 'misc',
                                        'sqs_workflow', 'sqs_workflow', 'tmp', 'result.json')

        while self.s3_helper.is_object_exist(s3_key) is False:
            print(f'no similarity on s3, {time.ctime()}')
            time.sleep(60)
        self.s3_helper.download_file_object_from_s3(s3_key, path_to_download)

        with open(path_to_download) as json_file:
            data = json.load(json_file)
        self.assertTrue(data['panos'][0]['hotspot'])

    def test_e2e_door_detection(self):
        # E2EUtils.purge_queue(self.processor.queue_url)
        # E2EUtils.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')

        inference_id = 'e2e-test-' + datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/cy2461o342/5eb33f7cf42b580e7aaa60f2/Tour/original-images/4624adl9ir.JPG",
            "tourId": "0123",
            "panoId": "0123"
        }

        self.processor.send_message_to_queue(json.dumps(preprocessing_message), self.processor.queue_url)
        logging.info('Preprocessing_message sent to queue')

        for i in range(120, 0, -1):
            print(i, end='\r')
            time.sleep(1)

        self.assertTrue(len(self.s3_helper.list_s3_objects(f'api/inference/DOOR_DETECTION/{inference_id}/')) == 1)
        print('done')

    def test_e2e_create_path_and_save_on_s3(self):
        logging.info('Test is starting')

        s3_helper = self.s3_helper
        s3_helper.s3_client.delete_object(Bucket=s3_helper.s3_bucket, Key='test/acl-test-1.txt')
        s3_helper.s3_client.delete_object(Bucket=s3_helper.s3_bucket, Key='test/acl-test-2.txt')
        logging.info('Messages are deleted on S3')

        acl1 = s3_helper.save_string_object_on_s3('test/acl-test-1.txt', 'test-body', 'document-test', True)
        acl2 = s3_helper.save_string_object_on_s3('test/acl-test-2.txt', 'test-body', 'document-test', False)

        r1 = str(requests.get(acl1))
        r2 = str(requests.get(acl2))

        self.assertTrue(r1 == '<Response [200]>')
        self.assertTrue(r2 == '<Response [403]>')

        logging.info('Test is finished')

    def test_e2e_object_detection(self):
        # E2EUtils.purge_queue(self.processor.queue_url)
        # E2EUtils.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')

        inference_id = 'e2e-test-' + datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.ObjectsDetecting.value,
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/cy2461o342/5eb33f7cf42b580e7aaa60f2/Tour/original-images/4624adl9ir.JPG",
            StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value],
            "tourId": "0123",
            "panoId": "0123"
        }
        assert self.processor.queue_url == 'https://eu-central-1.queue.amazonaws.com/700659137911/sandy-immoviewer-ai'
        self.processor.send_message_to_queue(json.dumps(preprocessing_message), self.processor.queue_url)
        logging.info('Preprocessing_message sent to queue')

        for i in range(120, 0, -1):
            print(i, end='\r')
            time.sleep(1)

        self.assertTrue(len(self.s3_helper.list_s3_objects(f'api/inference/OBJECTS_DETECTION/{inference_id}/')) == 1)
        print('done')
