from unittest import TestCase
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
import sys
import json
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock


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
            self.processor.create_result_s3_key('path_to_s3',
                                                'test_inference_type',
                                                'test_inference_id',
                                                'filename'),
            'path_to_s3/test_inference_type/test_inference_id/filename')

    def test_process_message_in_subprocess(self):
        self.assertIsNone(self.processor.process_message_in_subprocess('similarity', 'test-message-body'))
        self.assertIsNone(self.processor.process_message_in_subprocess('roombox', 'test-message-body'))

    def test_fail_in_subprocess(self):
        room_box_python = ""
        room_box_python_fail = ""
        similarity_python = ""
        similarity_python_fail = ""
        rmatrix_python = ""
        rmatrix_python_fail = ""
        door_detecting_python = ""
        door_detecting_python_fail = ""

        test_executables = {
            room_box_python: ProcessingTypesEnum.RoomBox,
            room_box_python_fail: ProcessingTypesEnum.RoomBox,
            similarity_python: ProcessingTypesEnum.Similarity,
            similarity_python_fail: ProcessingTypesEnum.Similarity,
            rmatrix_python: ProcessingTypesEnum.RMatrix,
            rmatrix_python_fail: ProcessingTypesEnum.RMatrix,
            door_detecting_python: ProcessingTypesEnum.DoorDetecting,
            door_detecting_python_fail: ProcessingTypesEnum.DoorDetecting,
        }

        for script, processing_type in test_executables:
            message = {"messageType": processing_type,
                       "panoUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                       "tourId": "5fa1df49014bf357cf250d52",
                       "panoId": "5fa1df55014bf357cf250d64"}
            message_str = str(json.dumps(message))
            print(f'message:{message_str}')
            self.processor.alert_service = AlertServiceMock()
            process_result = self.processor.run_process(sys.executable, script, message_str)

            self.assertTrue(process_result if 'fail' not in script else not process_result)
            if 'fail' in script:
                self.assertTrue(script in self.processor.alert_service.message)
                self.assertTrue(message_str in self.processor.alert_service.message)
                self.assertTrue(sys.executable in self.processor.alert_service.message)
            else:
                self.assertTrue(self.processor.alert_service.message is None)
