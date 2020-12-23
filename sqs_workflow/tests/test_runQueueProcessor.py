import json
from unittest import TestCase

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.RunProcessMock import RunProcessMock
from sqs_workflow.tests.TestUtils import TestUtils
from sqs_workflow.tests.test_sqsProcessor import TestSqsProcessor





class TestRunQueueProcessor(TestCase):

    def setUp(self) -> None:
        TestUtils.setup_environment_for_unit_tests()

    def test_run_queue_processor(self):
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties

        processor_mock = RunProcessMock()

        SqsProcessor.pull_messages = processor_mock.pull_messages_mock
        SqsProcessor.complete_processing_message = processor_mock.complete_processing_message_mock

        SqsProcessor.prepare_for_processing = processor_mock.prepare_for_processing_mock
        SqsProcessor.process_message_in_subprocess = processor_mock.process_message_in_subprocess_mock

        processor = SqsProcessor('-immoviewer-test')

        response = processor.run_queue_processor('-immoviewer-test')
        self.assertTrue('error' not in json.loads(processor_mock.message_body))

    # Prepare_for_processing is None
    def test_run_prep_for_proc_is_none(self):
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties

        processor_mock = RunProcessMock()

        SqsProcessor.pull_messages = processor_mock.pull_messages_mock
        SqsProcessor.complete_processing_message = processor_mock.complete_processing_message_mock

        SqsProcessor.prepare_for_processing = processor_mock.prepare_for_processing_none_mock
        SqsProcessor.process_message_in_subprocess = processor_mock.process_message_in_subprocess_mock

        SqsProcessor.list_of_messages = None

        processor = SqsProcessor('-immoviewer-test')

        response = processor.run_queue_processor('-immoviewer-test')
        print("********************")
        print(processor_mock.messages_queue[0])
        self.assertTrue(json.loads(processor_mock.messages_queue[0])[
                            'error'] == 'the JSON object must be str, bytes or bytearray, not NoneType')
