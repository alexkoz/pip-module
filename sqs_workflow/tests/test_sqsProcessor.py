from unittest import TestCase
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
import sys
import os
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock
from pathlib import Path
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


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
        common_path = os.path.join(str(Path.home()), 'projects', 'sqs_workflow', 'sqs_workflow', 'aids')

        room_box_python = common_path + '/dummy_roombox.py'
        room_box_python_fail = common_path + '/dummy_roombox_fail.py'
        similarity_python = common_path + '/dummy_similarity.py'
        similarity_python_fail = common_path + '/dummy_similarity_fail.py'
        rmatrix_python = common_path + '/dummy_rmatrix.py'
        rmatrix_python_fail = common_path + '/dummy_rmatrix_fail.py'
        door_detecting_python = common_path + '/dummy_dd.py'
        door_detecting_python_fail = common_path + '/dummy_dd_fail.py'

        test_executables = {
            room_box_python: ProcessingTypesEnum.RoomBox,  #
            room_box_python_fail: ProcessingTypesEnum.RoomBox,
            similarity_python: ProcessingTypesEnum.Similarity,
            similarity_python_fail: ProcessingTypesEnum.Similarity,
            rmatrix_python: ProcessingTypesEnum.RMatrix,
            rmatrix_python_fail: ProcessingTypesEnum.RMatrix,
            door_detecting_python: ProcessingTypesEnum.DoorDetecting,
            door_detecting_python_fail: ProcessingTypesEnum.DoorDetecting,
        }

        for script, processing_type in test_executables.items():
            message = {"messageType": processing_type,
                       "panoUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                       "tourId": "5fa1df49014bf357cf250d52",
                       "panoId": "5fa1df55014bf357cf250d64"}
            message_str = str(message)  # str(json.dumps(message))
            logging.info(f'message: {message_str}')
            self.processor.alert_service = AlertServiceMock()
            process_result = self.processor.run_process(sys.executable, script, message_str)
            logging.info(f'process_result: {process_result}')

            self.assertTrue(process_result == 'ok' if 'fail' not in script else process_result != 'ok')
            # if 'fail' in script:
            if process_result == 'fail':
                self.assertTrue(script in self.processor.alert_service.message)
                self.assertTrue(message_str in self.processor.alert_service.message)
                self.assertTrue(sys.executable in self.processor.alert_service.message)
            else:
                self.assertTrue(self.processor.alert_service.message is None)
