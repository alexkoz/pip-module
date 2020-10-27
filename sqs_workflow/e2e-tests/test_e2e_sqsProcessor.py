from unittest import TestCase
from sqs_workflow.SqsProcessor import SqsProcessor


class TestSqsProcessor(TestCase):
    def test_e2e(self):
        processor = SqsProcessor()

        req_receive = processor.receive_messages(2)
        req_send = processor.send_message('test_message_body')
        req_receive = processor.receive_messages(2)

        self.assertTrue(1 == 1)
