import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import TestCase

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.AlertServiceMock import AlertServiceMock
from sqs_workflow.tests.QueueMock import QueueMock
from sqs_workflow.tests.S3HelperMock import S3HelperMock
from sqs_workflow.tests.TestUtils import TestUtils
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.Utils import Utils
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor


class TestSqsProcessor(TestCase):
    test_list = []
    queue_mock_messages = []
    common_path = os.path.join(str(Path.home()),
                               'projects',
                               'python',
                               'misc',
                               'sqs_workflow',
                               'sqs_workflow')

    @staticmethod
    def define_sqs_queue_properties(sqs_client, sqs_resource, queue_name):
        return "queue_url", "queue_return_url", {}, {}

    @staticmethod
    def download_from_http(url: str, absolute_file_path=None) -> str:
        content = '{}'
        if os.path.exists(url):
            with open(url, 'r') as read_file:
                content = read_file.read()
                read_file.close()

        if absolute_file_path is not None:
            with open(absolute_file_path, 'w') as document_file:
                document_file.write(content)
                document_file.close()
        return content

    def setUp(self):
        TestUtils.setup_environment_for_unit_tests()
        Utils.download_from_http = TestSqsProcessor.download_from_http

        self.clear_local_directories()
        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties
        self.processor = SqsProcessor("-immoviewer-ai")

        self.processor.queue = QueueMock()
        self.processor.return_queue = QueueMock()

    def tearDown(self) -> None:
        self.clear_local_directories()

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

    def test_run_process(self):
        self.queue_mock_messages = None

        roombox_executable = sys.executable
        roombox_script = os.path.join(self.common_path, 'aids', 'dummy_roombox.py')

        roombox_result = '{"z0": 0, "z1": 0, "uv": [[0.874929459690343, 0.0499472701727508], [0.6246948329880218, 0.836521256741644], [0.6246948553348896, 0.04983696464707826], [0.8752748643537904, 0.8359191738972793], [0.3744601886079243, 0.04994725051497806], [0.12493895615154749, 0.8353210349449639], [0.12493893386684474, 0.05005729692317301], [0.37411478400664344, 0.83591919355491]]}'

        self.assertEqual(self.processor.run_process(roombox_executable,
                                                    roombox_script,
                                                    StringConstants.EXECUTABLE_PARAMS_KEY), roombox_result)

    @staticmethod
    def is_similarity_ready_document(s3_helper, message_object):
        input_path = os.path.join(SqsProcessor("-immoviewer-ai").input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(SqsProcessor("-immoviewer-ai").output_processing_directory,
                                   'fccc6d02b113260b57db5569e8f9c897')

        similarity_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Similarity.value,
                              StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                              StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                              StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                              StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                              StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value,
                                                          ProcessingTypesEnum.DoorDetecting.value],
                              StringConstants.INFERENCE_ID_KEY: "1111",
                              StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}

        similarity_message = json.dumps(similarity_message)
        return similarity_message

    def test_process_similarity_in_subprocess(self):

        def run_process_mock(executable: str, script: str, executable_params: str):
            return 'test_similarity_subprocess_output'

        def create_path_and_save_on_s3_mock(message_type: str,
                                            inference_id: str,
                                            processing_result: str,
                                            image_id: str,
                                            image_full_url='document',
                                            is_public=False):
            return 'test_s3_url_result'

        self.processor.run_process = run_process_mock
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        similarity_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Similarity.value,
                              StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                              StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                              StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                              StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                              StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value,
                                                          ProcessingTypesEnum.DoorDetecting.value],
                              StringConstants.INFERENCE_ID_KEY: "1111",
                              StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}

        similarity_message = json.dumps(similarity_message)

        def is_similarity_ready_none(s3_helper, message_object):
            print("similarity none")
            return None

        SimilarityProcessor.is_similarity_ready = is_similarity_ready_none
        self.assertIsNone(self.processor.process_message_in_subprocess(similarity_message))
        SimilarityProcessor.is_similarity_ready = self.is_similarity_ready_document

        result = json.loads(self.processor.process_message_in_subprocess(similarity_message))[
            'documentPath']

        self.assertTrue(result == 'test_s3_url_result')
        logging.info('test_process_similarity_in_subprocess is finished')

    def test_process_rotate_in_subprocess(self):

        def create_path_and_save_on_s3_mock(message_type: str,
                                            inference_id: str,
                                            processing_result: str,
                                            image_id: str,
                                            image_full_url='document',
                                            _public=False):
            return 'test_s3_url_result'

        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        self.processor.s3_helper = S3HelperMock([])
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock
        self.processor.create_output_file_on_s3 = create_output_file_on_s3_mock

        dir_input = os.path.join(self.common_path,
                                 'tmp',
                                 'input',
                                 '294ee74d8d88a37523c2e28e5c0e150c')

        dir_output = os.path.join(self.common_path,
                                  'tmp',
                                  'output',
                                  '294ee74d8d88a37523c2e28e5c0e150c')
        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        rotate_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Rotate.value,
                          StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                          StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                          StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                          StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                          StringConstants.STEPS_KEY: [ProcessingTypesEnum.Rotate.value],
                          StringConstants.INFERENCE_ID_KEY: "1111",
                          StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}
        rotate_message = json.dumps(rotate_message)

        response = json.loads(self.processor.process_message_in_subprocess(rotate_message))
        self.assertTrue(response['returnData'] == [[0.9987129910559471, -0.04888576451258531, -0.013510866889431278],[0.0489591807476533, 0.998788638594423, 0.0051531600847442875],[0.01316830223102185, -0.007323075477102751, 0.9998876283890858]])

    def test_process_roombox_in_subprocess(self):

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        def download_file_object_from_s3_mock(rotated_s3_result, input_path, url_hash, image_id):
            return 'rest'

        def download_fileobj_mock():
            return 'result'

        def check_pry_on_s3(message_type: str, url_hash: str, image_id: str):
            return '[[0.9987129910559471, -0.04888576451258531, -0.013510866889431278],[0.0489591807476533, 0.998788638594423, 0.0051531600847442875],[0.01316830223102185, -0.007323075477102751, 0.9998876283890858]]'

        self.s3_helper = S3HelperMock(['api/inference/ROTATE/294ee74d8d88a37523c2e28e5c0e150c/s7zu187383.JPG'])
        self.processor.s3_helper = self.s3_helper
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock
        self.processor.create_output_file_on_s3 = create_output_file_on_s3_mock
        self.s3_helper.download_file_object_from_s3 = download_file_object_from_s3_mock
        self.s3_helper.download_fileobj = download_fileobj_mock

        dir_input = os.path.join(self.processor.input_processing_directory,
                                 '294ee74d8d88a37523c2e28e5c0e150c')
        dir_output = os.path.join(self.processor.output_processing_directory,
                                  '294ee74d8d88a37523c2e28e5c0e150c')

        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        roombox_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RoomBox.value,
                           StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                           StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                           StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value],
                           StringConstants.INFERENCE_ID_KEY: "1111",
                           StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}
        roombox_message = json.dumps(roombox_message)

        self.processor.check_pry_on_s3 = check_pry_on_s3

        response = json.loads(self.processor.process_message_in_subprocess(roombox_message))
        self.assertTrue(response['returnData']['layout'])
        self.assertTrue(len(response['returnData']['layout']) == 8)  # as a number of points in "uv" in dummy_roombox

    def test_process_rmatrix_in_subprocess(self):

        def check_pry_on_s3_exists(message_type: str, url_hash: str, image_id: str):
            return '[[0.11, -0.22, -0.33],[0.44, 0.55, 0.66],[0.77, -0.88, 0.99]]'

        def check_pry_on_s3_none(message_type: str, url_hash: str, image_id: str):
            return None

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        def download_file_object_from_s3_mock(url_hash, image_id):
            return 'test_downloaded_rotated_result_from_s3'

        def download_fileobj_mock():
            return 'result'

        def rotated_result_on_s3_exists(rotated_s3_result):
            return True

        def rotated_result_on_s3_none(rotated_s3_result):
            return None

        self.s3_helper = S3HelperMock(['api/inference/ROTATE/294ee74d8d88a37523c2e28e5c0e150c/s7zu187383.JPG'])
        self.processor.s3_helper = self.s3_helper
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock
        self.processor.create_output_file_on_s3 = create_output_file_on_s3_mock
        self.s3_helper.download_file_object_from_s3 = download_file_object_from_s3_mock
        self.s3_helper.download_fileobj = download_fileobj_mock

        dir_input = os.path.join(self.processor.input_processing_directory,
                                 '294ee74d8d88a37523c2e28e5c0e150c')
        dir_output = os.path.join(self.processor.output_processing_directory,
                                  '294ee74d8d88a37523c2e28e5c0e150c')

        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        rmatrix_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RMatrix.value,
                           StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                           StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                           StringConstants.INFERENCE_ID_KEY: "1111",
                           StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}
        rmatrix_message = json.dumps(rmatrix_message)

        # PRY results exists on S3, Rotate doesn't exists on s3 -- output from dummy_rotate
        self.processor.check_pry_on_s3 = check_pry_on_s3_exists
        self.s3_helper.is_object_exist = rotated_result_on_s3_none

        response = json.loads(self.processor.process_message_in_subprocess(rmatrix_message))
        self.assertTrue(response['returnData'] == [[0.11, -0.22, -0.33],[0.44, 0.55, 0.66],[0.77, -0.88, 0.99]])

        # # PRY results exists on S3, Rotate exists on s3 -- output from rotated_result_on_s3
        self.processor.check_pry_on_s3 = check_pry_on_s3_exists
        self.s3_helper.is_object_exist = rotated_result_on_s3_exists

        response = json.loads(self.processor.process_message_in_subprocess(rmatrix_message))
        self.assertTrue(response['returnData'] == [[0.11, -0.22, -0.33],[0.44, 0.55, 0.66],[0.77, -0.88, 0.99]])

        # PRY results doesn't exists on S3, Rotate doesn't exists on s3 -- output from mock_pry
        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        self.processor.check_pry_on_s3 = check_pry_on_s3_none
        self.s3_helper.is_object_exist = rotated_result_on_s3_none

        response = json.loads(self.processor.process_message_in_subprocess(rmatrix_message))

        self.assertTrue(response['returnData'] == [[0.9987129910559471, -0.04888576451258531, -0.013510866889431278],[0.0489591807476533, 0.998788638594423, 0.0051531600847442875],[0.01316830223102185, -0.007323075477102751, 0.9998876283890858]])

        # PRY results doesn't exists on S3, Rotate exists on s3 -- output from rotated_result_on_s3
        self.processor.check_pry_on_s3 = check_pry_on_s3_none
        self.s3_helper.is_object_exist = rotated_result_on_s3_exists

        response = json.loads(self.processor.process_message_in_subprocess(rmatrix_message))
        self.assertTrue(response['returnData'] == [[0.9987129910559471, -0.04888576451258531, -0.013510866889431278],[0.0489591807476533, 0.998788638594423, 0.0051531600847442875],[0.01316830223102185, -0.007323075477102751, 0.9998876283890858]])

    def test_process_door_detection_in_subprocess(self):

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        def download_file_object_from_s3_mock(rotated_s3_result, input_path, url_hash, image_id):
            return 'rest'

        def download_fileobj_mock():
            return 'result'

        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties
        processor = SqsProcessor("-immoviewer-ai")
        processor.queue = QueueMock()
        processor.return_queue = QueueMock()

        processor.s3_helper = S3HelperMock(['api/inference/ROTATE/294ee74d8d88a37523c2e28e5c0e150c/s7zu187383.JPG'])
        processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock
        processor.create_output_file_on_s3 = create_output_file_on_s3_mock
        processor.s3_helper.download_file_object_from_s3 = download_file_object_from_s3_mock
        processor.s3_helper.download_fileobj = download_fileobj_mock

        dir_input = os.path.join(processor.input_processing_directory,
                                 '294ee74d8d88a37523c2e28e5c0e150c')
        dir_output = os.path.join(processor.output_processing_directory,
                                  '294ee74d8d88a37523c2e28e5c0e150c')

        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        input_path = os.path.join(processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        door_detection_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
                                  StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                                  StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                  StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                  StringConstants.INFERENCE_ID_KEY: "1111",
                                  StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}
        door_detection_message = json.dumps(door_detection_message)

        processing_result = processor.process_message_in_subprocess(door_detection_message)
        response = json.loads(processing_result)

        self.assertTrue(response['returnData'][0]['fileUrl'] == 'http://domen.com/img1.JPG')
        self.assertTrue(response['returnData'][0]['layout'])
        self.assertTrue(response['returnData'][1]['fileUrl'] == 'http://domen.com/img2.JPG')
        self.assertTrue(response['returnData'][1]['layout'])

    def test_process_objects_detection_in_subprocess(self):

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        def download_file_object_from_s3_mock(rotated_s3_result, input_path, url_hash, image_id):
            return 'rest'

        def download_fileobj_mock():
            return 'result'

        SqsProcessor.define_sqs_queue_properties = TestSqsProcessor.define_sqs_queue_properties
        processor = SqsProcessor("-immoviewer-ai")
        processor.queue = QueueMock()
        processor.return_queue = QueueMock()

        processor.s3_helper = S3HelperMock(['api/inference/ROTATE/294ee74d8d88a37523c2e28e5c0e150c/s7zu187383.JPG'])
        processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock
        processor.create_output_file_on_s3 = create_output_file_on_s3_mock
        processor.s3_helper.download_file_object_from_s3 = download_file_object_from_s3_mock
        processor.s3_helper.download_fileobj = download_fileobj_mock

        dir_input = os.path.join(processor.input_processing_directory,
                                 '294ee74d8d88a37523c2e28e5c0e150c')
        dir_output = os.path.join(processor.output_processing_directory,
                                  '294ee74d8d88a37523c2e28e5c0e150c')

        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        input_path = os.path.join(processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        objects_detection_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.ObjectsDetecting.value,
                                     StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                                     StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                     StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                     StringConstants.INFERENCE_ID_KEY: "1111",
                                     StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}
        objects_detection_message = json.dumps(objects_detection_message)

        processing_result = processor.process_message_in_subprocess(objects_detection_message)
        response = json.loads(processing_result)
        self.assertTrue(response['returnData'][0]['layout'][0]['id'] == 'indoor_objects_0_g0s6xk4c52')
        self.assertTrue(response['returnData'][0]['layout'][1]['id'] == 'indoor_objects_1_g0s6xk4c52')

    def send_message_to_queue_mock(self, message, queue_url):
        if self.queue_mock_messages is None:
            self.queue_mock_messages = []
        self.queue_mock_messages.append(message)

    def test_run_similarity(self):

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def is_similarity_ready_none_mock(s3_helper, message_object):
            return None

        self.queue_mock_messages = None
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        similarity_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Similarity.value,
                              StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                              StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                              StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                              StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                              StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value,
                                                          ProcessingTypesEnum.DoorDetecting.value],
                              StringConstants.INFERENCE_ID_KEY: "1111",
                              StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'}

        similarity_message = json.dumps(similarity_message)
        message_object = json.loads(similarity_message)

        SimilarityProcessor.is_similarity_ready = is_similarity_ready_none_mock

        response = self.processor.run_similarity(message_object, 'inference_id')
        # todo fix is_similarity_ready_none_mock
        # self.assertTrue(response['tourId'] == '1342240')  # as in dummy_similarity

    def test_run_preprocessing(self):
        self.queue_mock_messages = None

        # Copy json from test_assets folder to 'tmp' folder as "downloaded"
        origin_directory = os.path.join(self.common_path, 'test_assets', 'fccc6d02b113260b57db5569e8f9c897')
        dest_directory = os.path.join(self.common_path, 'tmp', 'input', 'fccc6d02b113260b57db5569e8f9c897')

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        shutil.copytree(origin_directory, dest_directory)
        os.makedirs(os.path.join(self.common_path, 'tmp', 'output'))

        preprocessing_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Preprocessing.value,
                                 StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                 StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                 StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                                 StringConstants.STEPS_KEY: [ProcessingTypesEnum.RoomBox.value],
                                 StringConstants.INFERENCE_ID_KEY: "3333",
                                 StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'
                                 }
        preprocessing_message = json.dumps(preprocessing_message)

        message_object = json.loads(preprocessing_message)
        inference_id = str(message_object[StringConstants.INFERENCE_ID_KEY])

        self.processor.send_message_to_queue = self.send_message_to_queue_mock

        self.processor.run_preprocessing(message_object, 'inference_id')

        self.assertTrue(len(self.queue_mock_messages) == 24)
        self.assertTrue(json.loads(self.queue_mock_messages[23])['messageType'] == 'SIMILARITY')
        logging.info('test_run_preprocessing is finished')

    def test_run_rmatrix(self):
        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        self.queue_mock_messages = None
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        rmatrix_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RMatrix.value,
                           StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                           StringConstants.INFERENCE_ID_KEY: "3333",
                           StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'
                           }
        rmatrix_message = json.dumps(rmatrix_message)
        message_object = json.loads(rmatrix_message)

        mock_rmatrix_output = '[[0.9987129910559471, -0.04888576451258531, -0.013510866889431278],' \
                              '[0.0489591807476533, 0.998788638594423, 0.0051531600847442875],' \
                              '[0.01316830223102185, -0.007323075477102751, 0.9998876283890858]]'

        self.assertTrue(
            self.processor.run_rmatrix(message_object, 'url_hash', 'image_id', 'image_full_url') == mock_rmatrix_output)
        logging.info('test_run_rmatrix is finished')

    def test_run_rotate(self):
        def create_output_file_on_s3_mock(ProcessingTypesEnum, url_hash, image_id, processing_result):
            return 'test_output_file_to_s3'

        dir_input = os.path.join(self.common_path,
                                 'tmp',
                                 'input',
                                 '294ee74d8d88a37523c2e28e5c0e150c')

        dir_output = os.path.join(self.common_path,
                                  'tmp',
                                  'output',
                                  '294ee74d8d88a37523c2e28e5c0e150c')
        if not os.path.exists(dir_input):
            os.makedirs(dir_input)
        if not os.path.exists(dir_output):
            os.makedirs(dir_output)

        test_absolute_path = os.path.join(dir_output,
                                          's7zu187383.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
            logging.info('Created temporary "image" file')

        self.queue_mock_messages = None
        self.processor.create_output_file_on_s3 = create_output_file_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        rotate_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Rotate.value,
                          StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                          StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                          StringConstants.INFERENCE_ID_KEY: "3333",
                          StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'
                          }
        rotate_message = json.dumps(rotate_message)
        message_object = json.loads(rotate_message)

        rotated_result = self.processor.run_rotate(message_object,
                                                   '294ee74d8d88a37523c2e28e5c0e150c',
                                                   's7zu187383.JPG',
                                                   'image_full_url')

        self.assertTrue(rotated_result['output'] == 'ok')

    def test_run_roombox(self):
        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return 'test_s3_url_result'

        def create_layout_object_mock(step: str, result: str):
            return 'result_test_create_layout_object'

        self.queue_mock_messages = None
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        roombox_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RoomBox.value,
                           StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                           StringConstants.INFERENCE_ID_KEY: "3333",
                           StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'
                           }
        roombox_message = json.dumps(roombox_message)
        message_object = json.loads(roombox_message)

        resp = self.processor.run_roombox(message_object, 'message_type', 'inference_id', 'image_id', 'image_full_url')

        # todo change self.similarity_processor.create_layout_object = create_layout_object_mock
        self.assertTrue(len(resp['layout']) == 8)  # as a number of points in "uv" in dummy_roombox

    def test_run_door_detection(self):

        def create_path_and_save_on_s3_mock(message_type: str, inference_id: str, processing_result: str, image_id: str,
                                            image_full_url='document', is_public=False):
            return {"test_s3_url_result": "value_test_s3_url_result_ok"}

        self.queue_mock_messages = None
        self.processor.create_path_and_save_on_s3 = create_path_and_save_on_s3_mock

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        door_detection_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.DoorDetecting.value,
                                  StringConstants.FILE_URL_KEY: "https://img.docusketch.com/items/s967284636/5fa1df49014bf357cf250d53/Tour/ai-images/s7zu187383.JPG",
                                  StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                                  StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                                  StringConstants.INFERENCE_ID_KEY: "3333",
                                  StringConstants.EXECUTABLE_PARAMS_KEY: f'--input_path {input_path} --output_path {output_path}'
                                  }
        door_detection_message = json.dumps(door_detection_message)
        message_object = json.loads(door_detection_message)

        response = self.processor.run_door_detecting(message_object, 'message_type', 'inference_id', 'image_id',
                                                     'image_full_url')
        self.assertTrue(response[0]['fileUrl'] == 'http://domen.com/img1.JPG')
        self.assertTrue(response[0]['layout'])
        self.assertTrue(response[1]['fileUrl'] == 'http://domen.com/img2.JPG')
        self.assertTrue(response[1]['layout'])

        logging.info('test_run_door_detection is finished')

    def test_fail_in_subprocess(self):

        self.processor.alert_service = AlertServiceMock()

        room_box_python = os.path.join(self.common_path, 'aids', 'dummy_roombox.py')
        room_box_python_fail = os.path.join(self.common_path, 'aids', 'dummy_roombox_fail.py')
        similarity_python = os.path.join(self.common_path, 'aids', 'dummy_similarity.py')
        similarity_python_fail = os.path.join(self.common_path, 'aids', 'dummy_similarity_fail.py')
        rmatrix_python = os.path.join(self.common_path, 'aids', 'dummy_rmatrix.py')
        rmatrix_python_fail = os.path.join(self.common_path, 'aids', 'dummy_rmatrix_fail.py')
        door_detecting_python = os.path.join(self.common_path, 'aids', 'dummy_dd.py')
        door_detecting_python_fail = os.path.join(self.common_path, 'aids', 'dummy_dd_fail.py')
        rotate_python = os.path.join(self.common_path, 'aids', 'dummy_rotate.py')
        rotate_python_fail = os.path.join(self.common_path, 'aids', 'dummy_rotate_fail.py')

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

            logging.info(f'script: {script}')

            process_result = self.processor.run_process(sys.executable,
                                                        script,
                                                        "--input_path /input/img.jpg --output_path /output/path/")
            logging.info(f'process_result: {process_result}')

            if "Process has failed" in  process_result:
                fail_counter += 1
            else:
                ok_counter += 1
        self.assertEqual(ok_counter, 5)  # because of dummy_Similarity returns layout array, not just 'ok'
        self.assertEqual(fail_counter, 5)

    def test_create_path_and_save_on_s3(self):
        s3_helper = S3HelperMock([])
        message_type = 'test-message-type'
        inference_id = 'test-inference-id'
        image_id = 'test-image-id'
        processing_result = 'test-processing-result-content'
        image_url = 'http://s3.com/path/image.jpg'
        self.processor.s3_helper = s3_helper
        s3_object = self.processor.create_path_and_save_on_s3(message_type,
                                                              inference_id,
                                                              processing_result,
                                                              image_id,
                                                              image_url)
        s3_key = os.path.join('api', 'inference', 'test-message-type', 'test-inference-id', 'test-image-id',
                              'result.json')
        # todo check tags
        self.assertTrue(
            'api/inference/test-message-type/test-inference-id/test-image-id/result.json' in s3_helper.existing_keys)
        self.assertTrue(
            s3_object[
                'url'] == 'https://TEST-BUCKET.s3-eu-west-1.amazonaws.com/api/inference/test-message-type/test-inference-id/test-image-id/result.json')

    @staticmethod
    def clear_local_directories():
        if os.path.isdir(os.environ['INPUT_DIRECTORY']):
            shutil.rmtree(os.environ['INPUT_DIRECTORY'])
            shutil.rmtree(os.environ['OUTPUT_DIRECTORY'])
            logging.info('Deleted all files from i/o directories')

    def test_prepare_for_processing_similarity(self):

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

    def test_prepare_for_processing_rotate(self):

        rotate_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.Rotate.value,
                          StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",
                          StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                          StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                          StringConstants.INFERENCE_ID_KEY: "3333",
                          }
        rotate_message = json.dumps(rotate_message)

        res_rotate_message = self.processor.prepare_for_processing(rotate_message)

        input_path = os.path.join(self.processor.input_processing_directory,
                                  '5a7ad1cae0be45937aa2101d2b643e62', 'n0l066b0r4.JPG')
        output_path = os.path.join(self.processor.output_processing_directory, '5a7ad1cae0be45937aa2101d2b643e62')

        self.assertTrue(json.loads(res_rotate_message)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_prepare_for_processing_rmatrix(self):

        rmatrix_message = {StringConstants.MESSAGE_TYPE_KEY: ProcessingTypesEnum.RMatrix.value,
                           StringConstants.FILE_URL_KEY: "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG",
                           StringConstants.TOUR_ID_KEY: "5fa1df49014bf357cf250d52",
                           StringConstants.PANO_ID_KEY: "5fa1df55014bf357cf250d64",
                           StringConstants.DOCUMENT_PATH_KEY: "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
                           StringConstants.INFERENCE_ID_KEY: "1111"}

        rmatrix_message = json.dumps(rmatrix_message)

        res_rmatrix_message = self.processor.prepare_for_processing(rmatrix_message)

        input_path = os.path.join(self.processor.input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(self.processor.output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        self.assertTrue(json.loads(res_rmatrix_message)[
                            'executable_params'] == f' --input_path {input_path} --output_path {output_path}')
        self.assertTrue(os.path.isfile(input_path))

    def test_create_output_file_on_s3(self):

        logging.info('Cleared S3 key folder on S3')

        # Creates test "image" file
        test_absolute_path = os.path.join(self.common_path,
                                          'test_assets',
                                          'tempfile_image.JPG')

        with open(test_absolute_path, 'w') as image_file:
            image_file.write('{}')
            image_file.close()
        logging.info('Created temporary "image" file')

        test_message_type = ProcessingTypesEnum.RoomBox.value
        test_image_hash = 'test-hash'
        image_id = '001'
        image_absolute_path = test_absolute_path
        self.processor.s3_helper = S3HelperMock([])
        s3_path = Utils.create_result_s3_key(StringConstants.COMMON_PREFIX,
                                             test_message_type,
                                             test_image_hash,
                                             "",
                                             image_id)

        self.processor.create_output_file_on_s3(test_message_type, test_image_hash, image_id, image_absolute_path)
        self.assertTrue(s3_path in self.processor.s3_helper.existing_keys)

    def test_fail_subprocess_run(self):

        def run_roombox_fail_mock(message_object, message_type, inference_id, image_id, image_full_url):
            executable = sys.executable
            script = os.path.join(os.getcwd(), 'sqs_workflow/sqs_workflow/aids/dummy_roombox_fail.py')
            subprocess_result = subprocess.run(executable + " " + script,
                                               shell=True,
                                               check=False,
                                               stdout=subprocess.PIPE)
            if not subprocess_result.returncode == 0:
                passed = False
                message = f'Process has failed for process:{executable} script:{script}.'
                assert passed, message

        self.processor.run_roombox = run_roombox_fail_mock

        self.assertRaises(AssertionError,
                          lambda: self.processor.run_roombox('message_object', 'message_type', 'inference_id',
                                                             'image_id', 'image_full_url'))