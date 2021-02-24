import concurrent.futures
import json
import logging
import os
import time
from pathlib import Path
from unittest import TestCase

import boto3

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor


class E2EAids(TestCase):
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

    def test_message_room_box(self):

        def pull_messages_mock(self, number_of_messages):
            class Message:
                body: str

                def delete(self):
                    pass
            message = Message()
            message.body = json.dumps({StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RoomBox.value,
                                           StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                           StringConstants.INFERENCE_ID_KEY: "3333",
                                           })
            return [message]

        SqsProcessor.pull_messages = pull_messages_mock
        SqsProcessor.run_queue_processor("-immoviewer-ai")
        pass

    def test_create_similarity_document(self):
        s3_helper = S3Helper()
        input_path = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow', 'sqs_workflow', 'tmp',
                                  'test_input_file.json')
        output_path = ''
        message_object = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Similarity.value,
                          StringConstants.STEPS_DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/preprocessing-no-layout_public_floors_data_from_01.06.2020/order_1012698_floor_-1.json",
                          StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value,
                                                      ProcessingTypesEnum.ObjectsDetecting.value,
                                                      ProcessingTypesEnum.DoorDetecting.value],
                          StringConstants.INFERENCE_ID_KEY: "e2e-inference/100",
                          StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}

        document_object = SimilarityProcessor.is_similarity_ready(s3_helper, message_object)
        print('finish')
        with open(os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow', 'sqs_workflow', 'tmp',
                               'test_result_similarity_file.json'), 'w') as outfile:
            json.dump(document_object, outfile)

    def test_load_e2e(self):
        bucket = "immoviewer-ai-test"
        prefix = "storage/segmentation/preprocessing-no-layout_public_floors_data_from_01.06.2020/"
        self.s3_helper.s3_bucket = bucket
        list_of_files = self.s3_helper.list_s3_objects(prefix)
        list_of_files = list_of_files[:40]
        inference_id = "e2e-inference/"
        message_index = 0
        messages = []
        for s3_file in list_of_files:
            if s3_file.endswith('.json'):
                document_url = f'https://{bucket}.s3-eu-west-1.amazonaws.com/{s3_file}'
                message_index = message_index + 1
                preprocessing_message = {
                    StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
                    "orderId": "5da5d5164cedfd0050363a2e",
                    "floor": 1,
                    "tourId": "1342386",
                    StringConstants.INFERENCE_ID_KEY: f"{inference_id}{str(message_index)}",
                    StringConstants.DOCUMENT_PATH_KEY: document_url,
                    StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value,
                                                ProcessingTypesEnum.DoorDetecting.value,
                                                ProcessingTypesEnum.ObjectsDetecting.value]
                }

                messages.append(preprocessing_message)
        self.processor.queue_url = 'https://eu-central-1.queue.amazonaws.com/700659137911/sandy-immoviewer-ai'
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
