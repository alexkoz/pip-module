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
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor


class TestSqsProcessor(TestCase):
    test_list = []
    queue_mock_messages = []
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
        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')
        #todo change to string constants
        similarity_message = '{"messageType": "SIMILARITY",\
                   "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                   "tourId": "5fa1df49014bf357cf250d52",\
                   "panoId": "5fa1df55014bf357cf250d64", \
                   "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                   "steps": ["ROOM_BOX", "DOOR_DETECTING"], \
                   "inferenceId": "1111"}'
        #todo change to string constants
        preprocessing_message = '{"messageType": "PREPROCESSING",\
                            "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                            "tourId": "5fa1df49014bf357cf250d52",\
                            "panoId": "5fa1df55014bf357cf250d64", \
                            "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                            "steps": ["ROOM_BOX"], \
                            "inferenceId": "3333", \
                            "executable_params": "' f'--input_path {input_path} --output_path {output_path}' '"}'

        self.assertIsNone(self.processor.process_message_in_subprocess(similarity_message))
        result = json.loads(self.processor.process_message_in_subprocess(preprocessing_message))

    @staticmethod
    def is_similarity_ready_true():
        return True

    @staticmethod
    def is_similarity_ready_false():
        return False

    def test_process_similarity_in_subprocess(self):
        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')
        #todo change to string constants
        similarity_message = f'{"messageType": "{ProcessingTypesEnum.Similarity.value}",\
                   "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                   "tourId": "5fa1df49014bf357cf250d52",\
                   "panoId": "5fa1df55014bf357cf250d64", \
                   "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                   "steps": ["ROOM_BOX", "DOOR_DETECTING"], \
                   "inferenceId": "1111"}'

        SimilarityProcessor.is_similarity_read = self.is_similarity_ready_false
        self.assertIsNone(self.processor.process_message_in_subprocess(similarity_message))
        SimilarityProcessor.is_similarity_read = self.is_similarity_ready_true
        self.assertIsNone(self.processor.process_message_in_subprocess(similarity_message))

    def send_message_to_queue_mock(self, message, queue_url):
        if self.queue_mock_messages is None:
            self.queue_mock_messages = []
        self.queue_mock_messages.append(message)

    def test_run_preprocessing(self):
        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        preprocessing_message = '{"messageType": "PREPROCESSING",\
                                    "fileUrl": "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",\
                                    "tourId": "5fa1df49014bf357cf250d52",\
                                    "panoId": "5fa1df55014bf357cf250d64", \
                                    "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json", \
                                    "steps": ["ROOM_BOX"], \
                                    "inferenceId": "3333", \
                                    "executable_params": "' f'--input_path {input_path} --output_path {output_path}' '"}'

        message_object = json.loads(preprocessing_message)
        inference_id = str(message_object[StringConstants.INFERENCE_ID_KEY])

        self.processor.send_message_to_queue = self.send_message_to_queue_mock

        self.processor.run_preprocessing(inference_id, message_object)
        self.assertTrue(len(self.queue_mock_messages) == 24)
        self.assertTrue(json.loads(self.queue_mock_messages[23])['messageType'] == 'SIMILARITY')
        logging.info('test_run_preprocessing is finished')

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
        s3_key = os.path.join('api', 'inference', 'test-message-type', 'test-inference-id', 'test-image-id',
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

        test_message_similarity = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Similarity.value,
                                   StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                   StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                   StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                                   StringConstants.STEPS_KEY: [ProcessingTypesEnum.Similarity.value],
                                   StringConstants.INFERENCE_ID_KEY: "1111"}

        test_message_similarity = json.dumps(test_message_similarity)

        res_similarity = self.processor.prepare_for_processing(test_message_similarity)
        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        self.assertTrue(json.loads(res_similarity)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_roombox(self):
        self.clear_local_directory(self.processor.input_processing_directory)
        self.clear_local_directory(self.processor.output_processing_directory)

        test_message_room_box = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RoomBox.value,
                                 StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",
                                 StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                 StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                 StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value],
                                 StringConstants.INFERENCE_ID_KEY: "222"}

        test_message_room_box = json.dumps(test_message_room_box)

        res_room_box = self.processor.prepare_for_processing(test_message_room_box)
        input_path = os.path.join(self.processor.input_processing_directory,
                                  '5a7ad1cae0be45937aa2101d2b643e62', 'n0l066b0r4.JPG')
        output_path = os.path.join(self.processor.output_processing_directory,
                                   '5a7ad1cae0be45937aa2101d2b643e62')

        self.assertTrue(
            json.loads(res_room_box)['executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_door_detection(self):
        self.clear_local_directory(self.processor.input_processing_directory)
        self.clear_local_directory(self.processor.output_processing_directory)

        test_message_room_box = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
                                 StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",
                                 StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                 StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                 StringConstants.STEPS_KEY: [ProcessingTypesEnum.DoorDetecting.value],
                                 StringConstants.INFERENCE_ID_KEY: "222"}

        test_message_room_box = json.dumps(test_message_room_box)

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
        test_absolute_path = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow',
                                          'sqs_workflow', 'test_assets', 'tempfile_image.JPG')
        open(test_absolute_path, 'w').write('{}')
        logging.info('Created temporary "image" file')

        test_message_type = ProcessingTypesEnum.RoomBox.value
        test_image_hash = 'test-hash'
        image_id = '001'
        image_absolute_path = test_absolute_path

        self.processor.create_output_file_on_s3(test_message_type, test_image_hash, image_id, image_absolute_path)

        self.assertTrue(
            self.s3_helper.is_object_exist(os.path.join('api', 'inference', 'ROOM_BOX', 'test-hash', '001')))

    def test_run_process(self):
        roombox_executable = os.environ[f'{ProcessingTypesEnum.RoomBox.value}_EXECUTABLE']
        roombox_script = os.environ[f'{ProcessingTypesEnum.RoomBox.value}_SCRIPT']

        roombox_result = "[layout:[z0:0, z1:0, uv:[[0.874929459690343, 0.0499472701727508], [0.6246948329880218, 0.836521256741644], [0.6246948553348896, 0.04983696464707826], [0.8752748643537904, 0.8359191738972793], [0.3744601886079243, 0.04994725051497806], [0.12493895615154749, 0.8353210349449639], [0.12493893386684474, 0.05005729692317301], [0.37411478400664344, 0.83591919355491]]]], 25l187v00b_rotated.JPG:[:], models.json:[:], 25l187v00b_allpoints.png:[:], inference:[inference_id:7394979587235]]"

        self.assertEqual(self.processor.run_process(roombox_executable,
                                                    roombox_script,
                                                    StringConstants.EXECUTABLE_PARAMS_KEY), roombox_result)
