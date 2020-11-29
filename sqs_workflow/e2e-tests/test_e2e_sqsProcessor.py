import logging
import os
import random
import requests
import shutil
import subprocess
import sys
import time
import json
import boto3

from pathlib import Path
from unittest import TestCase
from os.path import dirname

from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor
from sqs_workflow.tests.test_sqsProcessor import TestSqsProcessor


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

    def test_read_write_messages(self):
        processor = SqsProcessor()

        self.purge_queue(self.processor.queue_url)
        req_receive = processor.receive_messages_from_queue(5)
        self.assertTrue(len(req_receive) == 0)

        for i in range(10):
            processor.send_message_to_queue(
                '{ \"inferenceId\":\"similarity-test\",  \"messageType\":\"similarity\", \"orderId\":' + str(i) + '}',
                self.processor.queue_url)

        req_receive = self.pull_messages(processor, 3)
        self.assertTrue(len(req_receive) == 3)

        for message in req_receive:
            processor.complete_processing_message(message)
        logging.info(f'len req_receive after delete = ', len(req_receive))

        req_receive = self.pull_messages(processor, 10)
        logging.info(f'len req_receive = ', len(req_receive))

        self.assertTrue(len(req_receive) == 7)
        logging.info('get attr values: ===================')

        for message in req_receive:
            req_get_attr = processor.get_attr_value(message, 'messageType')
            self.assertEqual(req_get_attr, 'similarity')

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

    def test_e2e(self):
        self.purge_queue(self.processor.queue_url)
        self.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')

        # inference_id = random.randint(5, 10)
        inference_id = '27-11-001'
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
            "orderId": "5da5d5164cedfd0050363a2e",
            "floor": 1,
            "tourId": "1342386",
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
            StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value]
        }
        # Sends message to queue
        self.processor.send_message_to_queue(json.dumps(preprocessing_message), self.processor.queue_url)
        logging.info('Preprocessing_message sent to queue')

        # Sleep 5 min
        time.sleep(65)  # 300 sec
        print('AFTER SLEEP')

        # todo check that similarity message is returned
        resp_return = self.processor.sqs_client.get_queue_attributes(QueueUrl=self.processor.queue_url,
                                                                     AttributeNames=['All'])
        similarity_message = None
        room_box_messages = []
        door_detection_messages = []

        while similarity_message is None:
            time.sleep(5)

            # Pulls messages from queue
            messages_in_return_queue = self.processor.pull_messages_from_return_queue(1)
            for message in messages_in_return_queue:
                if message[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.Similarity.value:
                    similarity_message = message
                    message.delete()
                    self.assertTrue(len(message[StringConstants.PANOS_KEY] == 4))
                elif message[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.RoomBox.value:
                    room_box_messages.append(message)
                    message.delete()
                elif message[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.DoorDetecting.value:
                    door_detection_messages.append(message)
                    message.delete()
                else:
                    assert 'Incorrect message type'

        # Preprocessing and processing messages
        json_message_object = self.processor.prepare_for_processing(json.dumps(similarity_message))
        json_similarity_message = json.loads(json_message_object)
        file_path = similarity_message[StringConstants.EXECUTABLE_PARAMS_KEY].replace('--input_path', '') \
            .split()[0].strip()

        with open(file_path) as f:
            json_message_object = json.load(f)

        list_json_messages = self.similarity_processor.start_pre_processing(json_similarity_message)
        # dirname(file_path))

        # Asserts similarity processed
        self.assertTrue(
            len(list_json_messages) == (len(preprocessing_message[StringConstants.STEPS_KEY]) * len(
                json_message_object[StringConstants.PANOS_KEY]) + 1))
        for json_message in list_json_messages:
            message_object = json.loads(json_message)
            if message_object[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.Similarity.value:
                self.assertTrue(len(message_object[StringConstants.STEPS_KEY]) == 2)
                self.assertTrue(StringConstants.DOCUMENT_PATH_KEY not in message_object)
            else:
                self.assertTrue(
                    message_object[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.DoorDetecting.value
                    or message_object[StringConstants.MESSAGE_TYPE_KEY] == ProcessingTypesEnum.RoomBox.value)

        self.assertTrue(len(list_json_messages) == len(room_box_messages))
        self.assertTrue(len(list_json_messages) == len(door_detection_messages))

        # todo check message type
        # todo if similarity -- check for similar
        # todo if not similarity -- append message to list w/ same type
        # todo delete message from return queue

        # todo assert similarity processed
        # todo len room_box_messages == num of panos
        # todo len door_detection_mesages == num of panos

    def test_e2e_door_detection(self):
        self.purge_queue(self.processor.queue_url)
        self.purge_queue(self.processor.return_queue_url)
        logging.info('Purged queues')

        inference_id = 999777
        preprocessing_message = {
            StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
            StringConstants.INFERENCE_ID_KEY: inference_id,
            StringConstants.PANO_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/cy2461o342/5eb33f7cf42b580e7aaa60f2/Tour/original-images/4624adl9ir.JPG",
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
