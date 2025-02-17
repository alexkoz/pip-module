import json
import os
from unittest import TestCase

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.TestUtils import TestUtils
from sqs_workflow.tests.test_sqsProcessor import TestSqsProcessor


class RunProcessMock:
    message_body = None
    list_of_messages = None
    messages_queue = None

    def __init__(self):
        TestUtils.setup_environment_for_unit_tests()
        pass

    def testdef(self, message_body):
        self.message_body = message_body

    def pull_messages_mock(self, number_of_messages) -> list:
        if self.list_of_messages is not None:
            return []

        self.list_of_messages = []

        input_processing_directory = os.environ['INPUT_DIRECTORY']
        output_processing_directory = os.environ['OUTPUT_DIRECTORY']

        input_path = os.path.join(input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        roombox_message = MessageMock()
        roombox_message.body = json.dumps(
            {"messageType": "SIMILARITY", "orderId": "5d36c94fc9e77c0054fbab02", "floor": 0,
             "documentPath": "https://immoviewer-ai-research.s3-eu-west-1.amazonaws.com/storage/segmentation/floors_data_from_01.06.2020_with_address/order_1013678_floor_1.json"})
        # roombox_message = json.dumps(roombox_message)
        self.list_of_messages.append(roombox_message)
        return self.list_of_messages

    def complete_processing_message_mock(self, message, message_body: str):
        # return f'sent_message_body_to_return_queue'
        self.messages_queue = [message_body]
        return self.messages_queue

    def prepare_for_processing_mock(self, message_body):
        return message_body

    def process_message_in_subprocess_mock(self, message_body):
        self.message_body = message_body
        return message_body

    def prepare_for_processing_none_mock(self, message_body):
        return None

    def process_message_in_subprocess_none_mock(self, message_body):
        return None


class MessageMock:
    def __init__(self):
        self.body = ''


class TestRun(TestCase):
    # No exception
    def test_run_queue_processor(self):
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties

        processor_mock = RunProcessMock()
        processor = SqsProcessor('-immoviewer-test')
        processor.pull_messages = processor_mock.pull_messages_mock
        processor.complete_processing_message = processor_mock.complete_processing_message_mock

        processor.prepare_for_processing = processor_mock.prepare_for_processing_mock
        processor.process_message_in_subprocess = processor_mock.process_message_in_subprocess_mock



        response = processor.run_queue_processor('-immoviewer-test')
        #todo thing about how to redefine method
        #self.assertTrue('error' not in json.loads(processor_mock.message_body))

    # Process_message_in_subprocess is None
    def test_run_proc_message_in_subproc_is_none(self):
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties

        processor_mock = RunProcessMock()
        processor = SqsProcessor('-immoviewer-test')
        processor.pull_messages = processor_mock.pull_messages_mock
        processor.complete_processing_message = processor_mock.complete_processing_message_mock

        processor.prepare_for_processing = processor_mock.prepare_for_processing_mock
        processor.process_message_in_subprocess = processor_mock.process_message_in_subprocess_none_mock

        processor.list_of_messages = None

        response = processor.run_queue_processor('-mock-queue-name')
        self.assertTrue(response is None)

    # Process_message_in_subprocess is None, prepare_for_processing is None
    def test_proc_message_and_prepare_for_proc_both_none(self):
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties

        processor_mock = RunProcessMock()
        processor = SqsProcessor('-immoviewer-test')
        processor.pull_messages = processor_mock.pull_messages_mock
        processor.complete_processing_message = processor_mock.complete_processing_message_mock

        processor.prepare_for_processing = processor_mock.prepare_for_processing_none_mock
        processor.process_message_in_subprocess = processor_mock.process_message_in_subprocess_none_mock

        processor.list_of_messages = None

        response = processor.run_queue_processor('-mock-queue-name')
        self.assertTrue(response is None)

