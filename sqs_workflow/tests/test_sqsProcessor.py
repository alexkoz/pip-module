import logging
import os
import sys
from pathlib import Path
from unittest import TestCase
import shutil
import json

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.Utils import Utils

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class TestSqsProcessor(TestCase):
    test_list = []
    processor = SqsProcessor()
    s3_helper = S3Helper()
    processor.queue = QueueMock()
    processor.return_queue = QueueMock()

    def test_send_message(self):
        message_body = "message_body_"
        for i in range(8):
            self.processor.queue.send_message(message_body=message_body + str(i), queue_url=os.environ['QUEUE_LINK'])
        self.assertTrue(self.processor.queue.queue_messages[6]['Body'] == 'message_body_6')

    def test_receive_mock_messages(self):
        self.processor.queue.receive_messages(5)
        self.assertTrue(len(self.processor.queue.queue_messages) == 5)

    def test_delete_message(self):
        class TestMessage:
            def __init__(self):
                body = None

        test_message_1 = TestMessage()
        test_message_1.body = 'text-1'
        test_message_2 = TestMessage()
        test_message_2.body = 'text-2'
        test_message_3 = TestMessage()
        test_message_3.body = 'text-3'
        self.processor.send_message(test_message_1, os.environ['QUEUE_LINK'])
        self.processor.send_message(test_message_2, os.environ['QUEUE_LINK'])
        self.processor.send_message(test_message_3, os.environ['QUEUE_LINK'])

        self.processor.complete_processing_message('text-2')
        self.assertTrue(len(self.processor.queue.queue_messages) == 2)

    def test_create_result_s3_key(self):
        self.assertEqual(
            Utils.create_result_s3_key('path_to_s3',
                                       'test_inference_type',
                                       'test_inference_id',
                                       'test_image_id',
                                       'filename'),
            'path_to_s3/test_inference_type/test_inference_id/test_image_id/filename')

    def test_process_message_in_subprocess(self):
        message1 = '{"messageType": "SIMILARITY",\
                   "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                   "tourId": "5fa1df49014bf357cf250d52",\
                   "panoId": "5fa1df55014bf357cf250d64", \
                   "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                   "steps": ["SIMILARITY"], \
                   "inferenceId": "1111"}'
        message2 = '{"messageType": "ROOM_BOX",\
                    "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                    "tourId": "5fa1df49014bf357cf250d52",\
                    "panoId": "5fa1df55014bf357cf250d64", \
                    "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                    "steps": ["ROOM_BOX"], \
                    "inferenceId": "2222"}'
        self.assertIsNone(self.processor.process_message_in_subprocess(StringConstants.SIMILARITY_KEY, message1))
        # self.assertIsNone(self.processor.process_message_in_subprocess(StringConstants.ROOM_BOX_KEY, message2))

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
        ok_counter = 0
        fail_counter = 0

        for script, processing_type in test_executables.items():
            message = {"messageType": processing_type,
                       "panoUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                       "tourId": "5fa1df49014bf357cf250d52",
                       "panoId": "5fa1df55014bf357cf250d64"}
            message_str = str(message)
            logging.info(f'script: {script}')
            logging.info(f'message: {message_str}')
            self.processor.alert_service = AlertServiceMock()
            process_result = self.processor.alert_service.run_process(sys.executable, script, message_str)
            logging.info(f'process_result: {process_result}')

            if process_result == 'ok':
                ok_counter += 1
            elif process_result == 'fail':
                fail_counter += 1
        self.assertEqual(ok_counter, 3)  # because of dummy_Similarity returns layout array, not just 'ok'
        self.assertEqual(fail_counter, 4)

    def clear_directory(self, path_to_folder_in_bucket: str):
        sync_command = f"aws s3 --profile {os.environ['AWS_PROFILE']} rm s3://{os.environ['S3_BUCKET']}/{path_to_folder_in_bucket} --recursive"
        logging.info(f'sync command: {sync_command}')
        stream = os.popen(sync_command)
        output = stream.read()
        logging.info(f'output: {output}')

    def test_create_path_and_save_on_s3(self):
        s3_helper = self.s3_helper
        message_type = 'test-message-type'
        inference_id = 'test-inference-id'
        processing_result = 'test-processing-result-content'
        self.processor.create_path_and_save_on_s3(message_type, inference_id, processing_result)
        s3_key = 'api/inference/test-message-type/test-inference-id/asset/'
        self.assertTrue(s3_helper.is_object_exist(s3_key))

    def clear_local_directory(self, path_in_project):
        if os.path.isdir(os.path.join(os.getcwd(), path_in_project, 'input')):
            shutil.rmtree(os.path.join(os.getcwd(), path_in_project, 'input'))
            shutil.rmtree(os.path.join(os.getcwd(), path_in_project, 'output'))
            logging.info('Deleted all files from i/o directories')

    def test_prepare_for_processing_similarity(self):
        self.clear_local_directory('tmp/')

        test_message_similarity = '{"messageType": "SIMILARITY",\
                           "tourId": "5fa1df49014bf357cf250d52",\
                           "panoId": "5fa1df55014bf357cf250d64", \
                           "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                           "steps": ["SIMILARITY"], \
                           "inferenceId": "1111"}'

        res_similarity = self.processor.prepare_for_processing(test_message_similarity)
        input_path = os.path.join(os.getcwd(), 'tmp', 'input',
                                  'ad7ede0d6d45f7dc4656763b87b81db2') + '/order_1012550_floor_1.json.json'
        output_path = os.path.join(os.getcwd(), 'tmp', 'output', 'ad7ede0d6d45f7dc4656763b87b81db2')

        self.assertTrue(json.loads(res_similarity)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_roombox(self):
        self.clear_local_directory('tmp/')

        test_message_room_box = '{"messageType": "ROOM_BOX",\
                           "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",\
                           "tourId": "5fa1df49014bf357cf250d52",\
                           "panoId": "5fa1df55014bf357cf250d64", \
                           "steps": ["ROOM_BOX"], \
                           "inferenceId": "222"}'

        res_room_box = self.processor.prepare_for_processing(test_message_room_box)
        input_path = os.path.join(os.getcwd(), 'tmp', 'input', 'e52d12ec195bea3977909c8ae585e5b6') + '/n0l066b0r4.JPG'
        output_path = os.path.join(os.getcwd(), 'tmp', 'output', 'e52d12ec195bea3977909c8ae585e5b6')

        self.assertTrue(
            json.loads(res_room_box)['executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_door_detection(self):
        self.clear_local_directory('tmp/')

        test_message_room_box = '{"messageType": "DOOR_DETECTION",\
                               "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",\
                               "tourId": "5fa1df49014bf357cf250d52",\
                               "panoId": "5fa1df55014bf357cf250d64", \
                               "steps": ["DOOR_DETECTION"], \
                               "inferenceId": "222"}'

        res_door_detection = self.processor.prepare_for_processing(test_message_room_box)
        input_path = os.path.join(os.getcwd(), 'tmp', 'input', 'e52d12ec195bea3977909c8ae585e5b6') + '/n0l066b0r4.JPG'
        output_path = os.path.join(os.getcwd(), 'tmp', 'output', 'e52d12ec195bea3977909c8ae585e5b6')

        self.assertTrue(json.loads(res_door_detection)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))
