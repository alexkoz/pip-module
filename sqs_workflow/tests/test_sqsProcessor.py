from unittest import TestCase
from sqs_workflow.SqsProcessor import SqsProcessor
from sqs_workflow.tests.QueueMock import QueueMock


class TestSqsProcessor(TestCase):
    test_list = []
    processor = SqsProcessor()
    processor.queue = QueueMock()

    def test_send_message(self):
        message_body = "message_body_"
        for i in range(8):
            self.processor.send_message(message_body=message_body + str(i))
        self.assertTrue(self.processor.queue.queue_messages[6]['Body'] == 'message_body_6')

    def test_receive_mock_messages(self):
        self.processor.receive_messages(5)
        self.assertTrue(len(self.processor.queue.queue_messages) == 5)

    def test_delete_message(self):
        self.processor.send_message('text-1')
        self.processor.send_message('text-2')
        self.processor.send_message('text-3')

        self.processor.delete_message('text-2')
        self.assertTrue(len(self.processor.queue.queue_messages) == 2)



