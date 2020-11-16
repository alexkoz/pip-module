from unittest import TestCase
from sqs_workflow.tests.QueueMock import QueueMock


class TestQueueMock(TestCase):
    def test_receive_mock_messages(self):
        test_queue = QueueMock()

        test_queue.receive_messages(3)
        self.assertTrue(len(test_queue.queue_messages) == 3)

    def test_send_message(self):
        test_queue = QueueMock()

        body_text = 'New-body-text'
        test_queue.send_message(body_text, '')
        self.assertTrue(test_queue.queue_messages[0]['Body'] == body_text)

    def test_delete_message(self):
        test_queue = QueueMock()

        test_queue.send_message('text-1', '')
        test_queue.send_message('text-2', '')
        test_queue.send_message('text-3', '')

        test_queue.delete_message('text-2')
        self.assertTrue(len(test_queue.queue_messages) == 2)
