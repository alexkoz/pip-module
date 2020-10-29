from unittest import TestCase
from sqs_workflow.SqsProcessor import SqsProcessor
import time


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
                time.sleep(2)
            print('attemps =', attemps)
        if attemps == 3:
            print('out of attemps')
        return list_of_messages

    def test_e2e(self):
        processor = SqsProcessor()

        processor.purge_queue()
        req_receive = processor.receive_messages(5)
        self.assertTrue(len(req_receive) == 0)

        for i in range(10):
            processor.send_message('test_message_body_' + str(i))

        req_receive = self.pull_messages(processor, 3)
        self.assertTrue(len(req_receive) == 3)

        for message in req_receive:
            processor.delete_message(message)
        print('len req_receive after delete = ', len(req_receive))

        req_receive = self.pull_messages(processor, 10)
        print('len req_receive = ', len(req_receive))

        self.assertTrue(len(req_receive) == 7)
