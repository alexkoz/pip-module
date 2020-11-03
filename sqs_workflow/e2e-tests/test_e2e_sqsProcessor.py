from unittest import TestCase
from sqs_workflow.SqsProcessor import SqsProcessor
from sqs_workflow.aws.s3.S3Helper import S3Helper
import time
import os
import subprocess
import sys


class TestSqsProcessor(TestCase):

    def pull_messages(self, processor: SqsProcessor, number_of_messages: int) -> list:
        attemps = 0
        list_of_messages = processor.receive_messages(number_of_messages)
        while attemps < 7 and len(list_of_messages) < number_of_messages:
            messages_received = processor.receive_messages(1)
            if len(messages_received) > 0:
                list_of_messages += messages_received
                print('len list of messgrs = ', len(list_of_messages))
            else:
                attemps += 1
                time.sleep(1)
            print('attemps =', attemps)
        if attemps == 3:
            print('out of attemps')
        return list_of_messages

    def test_read_write_messages(self):
        processor = SqsProcessor()

        processor.purge_queue()
        req_receive = processor.receive_messages(5)
        self.assertTrue(len(req_receive) == 0)

        for i in range(10):
            processor.send_message(
                '{ \"inferenceId\":\"similarity-test\",  \"messageType\":\"similarity\", \"orderId\":' + str(i) + '}')

        req_receive = self.pull_messages(processor, 3)
        self.assertTrue(len(req_receive) == 3)

        for message in req_receive:
            processor.delete_message(message)
        print('len req_receive after delete = ', len(req_receive))

        req_receive = self.pull_messages(processor, 10)
        print('len req_receive = ', len(req_receive))

        self.assertTrue(len(req_receive) == 7)
        print('get attr values: ===================')

        for message in req_receive:
            req_get_attr = processor.get_attr_value(message, 'messageType')
            self.assertEqual(req_get_attr, 'similarity')

    def test_e2e(self):
        s3_helper = S3Helper()
        s3_helper.clear_directory('api/inference/similarity/similarity')
        processor = SqsProcessor()

        processor.purge_queue()
        req_receive = processor.receive_messages(5)
        self.assertTrue(len(req_receive) == 0)

        for i in range(10):
            processor.send_message(
                '{ \"inferenceId\":\"similarity\", \"messageType\":\"similarity\", \"orderId\":' + str(i) + '}')

        for i in range(10):
            subprocess.run([sys.executable,  # path to python
                            '/Users/alexkoz/projects/sqs_workflow/sqs_workflow/main.py'],  # path to MAIN
                           universal_newlines=True)
        self.assertTrue(s3_helper.is_processing_complete('api/inference/similarity/similarity', 10))
