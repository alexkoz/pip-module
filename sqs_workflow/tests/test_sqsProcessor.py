from unittest import TestCase
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
import sys
import os
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock
from pathlib import Path
import logging
from sqs_workflow.aws.s3.S3Helper import S3Helper

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
        message1 = '{"messageType": "SIMILARITY",\
                   "panoUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                   "tourId": "5fa1df49014bf357cf250d52",\
                   "panoId": "5fa1df55014bf357cf250d64"}'
        message2 = '{"messageType": "ROOMBOX",\
                    "panoUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                    "tourId": "5fa1df49014bf357cf250d52",\
                    "panoId": "5fa1df55014bf357cf250d64"}'
        self.assertIsNone(self.processor.process_message_in_subprocess('SIMILARITY', message1))
        self.assertIsNone(self.processor.process_message_in_subprocess('ROOMBOX', message2))

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

    def clear_directory(self, path_to_folder_in_bucket: str):
        sync_command = f"aws s3 --profile {os.environ['AWS_PROFILE']} rm s3://{os.environ['S3_BUCKET']}/{path_to_folder_in_bucket} --recursive"
        logging.info(f'sync command: {sync_command}')
        stream = os.popen(sync_command)
        output = stream.read()
        logging.info(f'output: {output}')


    #todo create s3helper mock
    #todo change to work without real aws s3
    #todo transfer to e2e
    def test_check_pry_on_s3(self):
        s3_helper = S3Helper()
        processor = SqsProcessor()
        self.clear_directory('api/inference/')
        processor.purge_queue()

        # Checks that no result.json in S3 in subfolder test-hash-001
        test_message = {'panoUrl': 1234,
                        'url_hash': 'test-hash-001'}
        self.assertIsNone(processor.check_pry_on_s3(test_message))

        # Adds a result.json file in S3 in subfolder test-hash-002
        s3_path = processor.create_result_s3_key('api/inference/', 'R_MATRIX', 'test-hash-002', 'result.json')
        s3_helper.save_object_on_s3(s3_path, 'test-body-content')

        # Checks that result.json exists in S3 in subfolder test-hash-002
        test_message = {'panoUrl': 1235,
                        'url_hash': 'test-hash-002'}
        self.assertEqual(processor.check_pry_on_s3(test_message), 'test-body-content')



