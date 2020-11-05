from unittest import TestCase
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
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

    def test_create_result_s3_key(self):
        self.assertEqual(
            self.processor.create_result_s3_key('path_to_s3', 'test_inference_type', 'test_inference_id', 'filename'),
            'path_to_s3/test_inference_type/test_inference_id/filename')

    def test_process_message_in_subprocess(self):
        self.assertIsNone(self.processor.process_message_in_subprocess('similarity', 'test-message-body'))
        self.assertIsNone(self.processor.process_message_in_subprocess('roombox', 'test-message-body'))
