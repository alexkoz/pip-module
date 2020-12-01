import json
import logging
import os
import shutil
import sys
from pathlib import Path
from unittest import TestCase

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.Utils import Utils
from sqs_workflow.utils.StringConstants import StringConstants


class TestSqsProcessor(TestCase):
    test_list = []
    processor = SqsProcessor("-immoviewer-ai")
    s3_helper = S3Helper()
    processor.queue = QueueMock()
    processor.return_queue = QueueMock()

    def test_send_message(self):
        self.processor.queue = QueueMock()
        message_body = "message_body_"
        for i in range(8):
            self.processor.queue.send_message_to_queue(message_body=message_body + str(i),
                                                       queue_url=os.environ['APP_BRANCH'])
        self.assertTrue(self.processor.queue.queue_messages[6]['Body'] == 'message_body_6')

    def test_receive_mock_messages(self):
        self.processor.queue = QueueMock()
        self.processor.queue.receive_messages_from_queue(5)
        self.assertTrue(len(self.processor.queue.queue_messages) == 5)

    def test_delete_message(self):
        self.processor.queue = QueueMock()
        test_message_1 = '{"message": "test-1"}'
        test_message_2 = '{"message": "test-2"}'
        test_message_3 = '{"message": "test-3"}'

        self.processor.queue.send_message_to_queue(test_message_1, 'test-queue-url')
        self.processor.queue.send_message_to_queue(test_message_2, 'test-queue-url')
        self.processor.queue.send_message_to_queue(test_message_3, 'test-queue-url')

        self.processor.queue.complete_processing_message('{"message": "test-2"}')
        self.assertTrue(len(self.processor.queue.queue_messages) == 2)

    def test_create_result_s3_key(self):
        should_be_created_path = os.path.join('path_to_s3', 'test_inference_type', 'test_inference_id', 'test_image_id',
                                              'filename')
        self.assertEqual(
            Utils.create_result_s3_key('path_to_s3',
                                       'test_inference_type',
                                       'test_inference_id',
                                       'test_image_id',
                                       'filename'),
            should_be_created_path)

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
        self.assertIsNone(self.processor.process_message_in_subprocess(message1))

    def test_fail_in_subprocess(self):

        common_path = os.path.join(str(Path.home()),
                                   'projects',
                                   'python',
                                   'misc',
                                   'sqs_workflow',
                                   'sqs_workflow',
                                   'aids')

        room_box_python = os.path.join(common_path, 'dummy_roombox.py')
        room_box_python_fail = os.path.join(common_path, 'dummy_roombox_fail.py')
        similarity_python = os.path.join(common_path, 'dummy_similarity.py')
        similarity_python_fail = os.path.join(common_path, 'dummy_similarity_fail.py')
        rmatrix_python = os.path.join(common_path, 'dummy_rmatrix.py')
        rmatrix_python_fail = os.path.join(common_path, 'dummy_rmatrix_fail.py')
        door_detecting_python = os.path.join(common_path, 'dummy_dd.py')
        door_detecting_python_fail = os.path.join(common_path, 'dummy_dd_fail.py')
        rotate_python = os.path.join(common_path, 'dummy_rotate.py')
        rotate_python_fail = os.path.join(common_path, 'dummy_rotate_fail.py')

        test_executables = {
            room_box_python: ProcessingTypesEnum.RoomBox.value,  #
            room_box_python_fail: ProcessingTypesEnum.RoomBox.value,
            similarity_python: ProcessingTypesEnum.Similarity.value,
            similarity_python_fail: ProcessingTypesEnum.Similarity.value,
            rmatrix_python: ProcessingTypesEnum.RMatrix.value,
            rmatrix_python_fail: ProcessingTypesEnum.RMatrix.value,
            door_detecting_python: ProcessingTypesEnum.DoorDetecting.value,
            door_detecting_python_fail: ProcessingTypesEnum.DoorDetecting.value,
            rotate_python: ProcessingTypesEnum.Rotate.value,
            rotate_python_fail: ProcessingTypesEnum.Rotate.value
        }
        ok_counter = 0
        fail_counter = 0

        for script, processing_type in test_executables.items():
            message = {StringConstants.MESSAGE_TYPE_KEY: processing_type,
                       StringConstants.PANO_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                       StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                       StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64"}
            message_str = str(message)
            logging.info(f'script: {script}')
            logging.info(f'message: {message_str}')
            self.processor.alert_service = AlertServiceMock()
            process_result = self.processor.alert_service.run_process(sys.executable, script, message_str)
            logging.info(f'process_result: {process_result}')

            if process_result == 'fail':
                fail_counter += 1
            else:
                ok_counter += 1
        self.assertEqual(ok_counter, 5)  # because of dummy_Similarity returns layout array, not just 'ok'
        self.assertEqual(fail_counter, 5)

    @staticmethod
    def clear_directory(path_to_folder_in_bucket: str):
        sync_command = f"aws s3 --profile {os.environ['AWS_PROFILE']} rm s3://{os.environ['S3_BUCKET']}/{path_to_folder_in_bucket} --recursive"
        logging.info(f'sync command: {sync_command}')
        stream = os.popen(sync_command)
        output = stream.read()
        logging.info(f'output: {output}')

    def test_create_path_and_save_on_s3(self):
        s3_helper = self.s3_helper
        message_type = 'test-message-type'
        inference_id = 'test-inference-id'
        image_id = 'test-image-id'
        processing_result = 'test-processing-result-content'
        image_url = 'http://s3.com/path/image.jpg'
        self.processor.create_path_and_save_on_s3(message_type,
                                                  inference_id,
                                                  processing_result,
                                                  image_id,
                                                  image_url)
        s3_key = os.path.join('api', 'inference', 'test-message-type', ',test-inference-id', 'test-image-id',
                              'result.json')
        # todo check tags
        self.assertTrue(s3_helper.is_object_exist(s3_key))

    @staticmethod
    def clear_local_directory(path_in_project):
        if os.path.isdir(os.environ['INPUT_DIRECTORY']):
            shutil.rmtree(os.environ['INPUT_DIRECTORY'])
            shutil.rmtree(os.environ['OUTPUT_DIRECTORY'])
            logging.info('Deleted all files from i/o directories')

    def test_prepare_for_processing_similarity(self):
        self.clear_local_directory(self.processor.input_processing_directory)
        self.clear_local_directory(self.processor.output_processing_directory)

        test_message_similarity = '{"messageType": "SIMILARITY",\
                           "tourId": "5fa1df49014bf357cf250d52",\
                           "panoId": "5fa1df55014bf357cf250d64", \
                           "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                           "steps": ["SIMILARITY"], \
                           "inferenceId": "1111"}'

        res_similarity = self.processor.prepare_for_processing(test_message_similarity)
        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897') + '/order_1012550_floor_1.json.json'
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        self.assertTrue(json.loads(res_similarity)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

        # " --input_path /Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/tmp/input/fccc6d02b113260b57db5569e8f9c897/order_1012550_floor_1.json.json --output_path /Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/tmp/output/fccc6d02b113260b57db5569e8f9c897"
        #                /Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/tmp/input/ad7ede0d6d45f7dc4656763b87b81db2/order_1012550_floor_1.json.json'

    def test_prepare_for_processing_roombox(self):
        self.clear_local_directory(self.processor.input_processing_directory)
        self.clear_local_directory(self.processor.output_processing_directory)

        test_message_room_box = '{"messageType": "ROOM_BOX",\
                           "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",\
                           "tourId": "5fa1df49014bf357cf250d52",\
                           "panoId": "5fa1df55014bf357cf250d64", \
                           "steps": ["ROOM_BOX"], \
                           "inferenceId": "222"}'

        res_room_box = self.processor.prepare_for_processing(test_message_room_box)
        input_path = os.path.join(self.processor.input_processing_directory,
                                  '5a7ad1cae0be45937aa2101d2b643e62') + '/n0l066b0r4.JPG'
        output_path = os.path.join(self.processor.output_processing_directory,
                                   '5a7ad1cae0be45937aa2101d2b643e62')

        self.assertTrue(
            json.loads(res_room_box)['executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_door_detection(self):
        self.clear_local_directory(self.processor.input_processing_directory)
        self.clear_local_directory(self.processor.output_processing_directory)

        test_message_room_box = '{"messageType": "DOOR_DETECTION",\
                               "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",\
                               "tourId": "5fa1df49014bf357cf250d52",\
                               "panoId": "5fa1df55014bf357cf250d64", \
                               "steps": ["DOOR_DETECTION"], \
                               "inferenceId": "222"}'
        tested = "f'{test_message_room_box}'"

        res_door_detection = self.processor.prepare_for_processing(test_message_room_box)
        input_path = os.path.join(self.processor.input_processing_directory,
                                  '5a7ad1cae0be45937aa2101d2b643e62', 'n0l066b0r4.JPG')
        output_path = os.path.join(self.processor.output_processing_directory, '5a7ad1cae0be45937aa2101d2b643e62')

        self.assertTrue(json.loads(res_door_detection)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_create_output_file_on_s3(self):
        self.clear_directory(os.path.join('api', 'inference', 'test-download-from-s3'))
        logging.info('Cleared S3 key folder on S3')

        # Creates test "image" file
        test_absolute_path = os.path.join(str(Path.home()), 'purge', 'tempfile_image.JPG')
        open(test_absolute_path, 'w').write('{}')
        logging.info('Created temporary "image" file')

        test_message_type = 'ROOM_BOX'
        test_image_hash = 'test-hash'
        image_id = '001'
        image_absolute_path = test_absolute_path

        self.processor.create_output_file_on_s3(test_message_type, test_image_hash, image_id, image_absolute_path)

        self.assertTrue(
            self.s3_helper.is_object_exist(os.path.join('api', 'inference', 'ROOM_BOX', 'test-hash', '001')))
