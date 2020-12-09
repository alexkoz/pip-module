import json
import logging
import os
import time
from unittest import TestCase
import datetime
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

    def test_all(self):

        message_body = '{"messageType": "SIMILARITY", "orderId": "5da5d5164cedfd0050363a2e", "floor": 1, "tourId": "1342386", "inferenceId": "inf_id_01", "steps": ["ROOM_BOX", "DOOR_DETECTION"], "fileUrl": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", "executable_params": " --input_path /home/ubuntu/purge/sqs_processing/input/fccc6d02b113260b57db5569e8f9c897/order_1012550_floor_1.json.json --output_path /home/ubuntu/purge/sqs_processing/output/fccc6d02b113260b57db5569e8f9c897", "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json"}'

        message_body = self.processor.prepare_for_processing(message_body)
        message_body = self.processor.process_message_in_subprocess(message_body)

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

    def test_e2e(self):
        # self.purge_queue(self.processor.queue_url)
        # self.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')
        document_url = "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/similarity/test_w_5_panos_without_layout.json"
        document_object = requests.get(document_url).json()

        inference_id = f'e2e-test-{datetime.datetime.now()}'.replace(' ', '').replace(':', '')
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
            "orderId": "5da5d5164cedfd0050363a2e",
            "floor": 1,
            "tourId": "1342386",
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.DOCUMENT_PATH_KEY: document_url,
            StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value]
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
        # todo wait till similarity is ready
        # todo while check s3 similarity result.
        # todo /api/inference/SIMILARITY/inferenceId/similarity/result.json
        similarity_step_results = self.s3_helper.list_s3_objects(os.path.join(StringConstants.COMMON_PREFIX,
                                                                              ProcessingTypesEnum.Similarity.value,
                                                                              inference_id))
        # todo download result when ready
        # todo parse json. 

    def test_e2e_door_detection(self):
        self.purge_queue(self.processor.queue_url)
        self.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')

        inference_id = 999777
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/cy2461o342/5eb33f7cf42b580e7aaa60f2/Tour/original-images/4624adl9ir.JPG",
            "tourId": "0123",
            "panoId": "0123"
        }

        self.processor.send_message_to_queue(json.dumps(preprocessing_message), self.processor.queue_url)
        logging.info('Preprocessing_message sent to queue')

        for i in range(300, 0, -1):
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
