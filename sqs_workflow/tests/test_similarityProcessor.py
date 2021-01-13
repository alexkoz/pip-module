import hashlib
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from unittest import TestCase
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.S3HelperMock import S3HelperMock
from sqs_workflow.tests.TestUtils import TestUtils
from sqs_workflow.tests.test_sqsProcessor import TestSqsProcessor
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.Utils import Utils
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class TestSimilarityProcessor(TestCase):
    similarity_processor = SimilarityProcessor()

    common_path = os.path.join(str(Path.home()),
                               'projects',
                               'python',
                               'misc',
                               'sqs_workflow',
                               'sqs_workflow')

    def setUp(self):
        TestUtils.setup_environment_for_unit_tests()
        Utils.download_from_http = TestSqsProcessor.download_from_http

    def test_create_layout_object(self):
        room_box_result = '{"z0": "0", "z1": "0", "uv": [[0.8942103326473919, 0.3353772676236854], [0.5747235927670448, 0.6223832045044406], [0.575059459160671, 0.37344853854460625], [0.8946108521103336, 0.6597705138137632], [0.4391388923396096, 0.3687213328274126], [0.08800329189223322, 0.6700959772611611], [0.08779664823660581, 0.3244858638081926], [0.4389803229974563, 0.6268292928215364]]}'
        layout_object = self.similarity_processor.create_layout_object(ProcessingTypesEnum.RoomBox.value,
                                                                       room_box_result)
        layout_object = json.loads(layout_object)
        list_of_corners = layout_object['layout']
        self.assertTrue(list_of_corners[0]['x'] == 141.9157197530611)

        self.assertTrue(list_of_corners[0]['y'] == -29.632091827736627)
        self.assertTrue(list_of_corners[0]['type'] == 'corner')

    def test_create_empty_layout_object(self):
        room_box_result = '{"z0": "0", "z1": "0", "uv": []}'
        layout_object = self.similarity_processor.create_layout_object(ProcessingTypesEnum.RoomBox.value,
                                                                       room_box_result)
        layout_object = json.loads(layout_object)
        list_of_corners = layout_object['layout']
        self.assertTrue(list_of_corners == [])

    def test_assemble_results_into_document(self):
        s3_helper_mock = S3HelperMock([])
        message_object = {
            StringConstants.FLOOR_ID_KEY: 1,
            "fpUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/map-images/1-floor-5i2cvu550f.jpg",
            StringConstants.PANOS_KEY: [
                {"createdDate": "16.07.2020 02:26:13",
                 "fileUrl": "http://domen.com/img1.JPG"},
                {"createdDate": "18.07.2020 02:43:15",
                 "fileUrl": "http://domen.com/img2.JPG"},
                {"createdDate": "18.07.2020 02:43:15",
                 "fileUrl": "http://domen.com/empty.JPG"}
            ]
        }

        list_result = [
            os.path.join('api', 'inference', ProcessingTypesEnum.RoomBox.value, '1111', 'img1.JPG', 'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.RoomBox.value, '1111', 'img2.JPG', 'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.RoomBox.value, '1111', 'empty.JPG', 'result.json'),

            os.path.join('api', 'inference', ProcessingTypesEnum.DoorDetecting.value, '1111', 'img1.JPG',
                         'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.DoorDetecting.value, '1111', 'img2.JPG',
                         'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.DoorDetecting.value, '1111', 'empty.JPG',
                         'result.json'),

            os.path.join('api', 'inference', ProcessingTypesEnum.ObjectsDetecting.value, '1111', 'img1.JPG',
                         'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.ObjectsDetecting.value, '1111', 'img2.JPG',
                         'result.json'),
            os.path.join('api', 'inference', ProcessingTypesEnum.ObjectsDetecting.value, '1111', 'empty.JPG',
                         'result.json'),

        ]

        new_message_object = SimilarityProcessor.assemble_results_into_document(s3_helper_mock, message_object,
                                                                                list_result)
        self.assertEqual(new_message_object['panos'][0]['fileUrl'], "http://domen.com/img1.JPG")
        self.assertEqual(new_message_object['panos'][1]['layout'][0]['type'], 'corner')
        self.assertEqual(new_message_object['panos'][1]['layout'][8]['id'], 'door_108')
        # todo door detector is apprriate with error
        # todo door detector is apprriate without error

    def test_start_pre_processing(self):
        message_object = {
            StringConstants.FLOOR_ID_KEY: 1,
            "fpUrl": "url",
            StringConstants.PANOS_KEY: [
                'pano1', 'pano2'
            ],
            StringConstants.EXECUTABLE_PARAMS_KEY: '--input_path ' + os.path.join(str(Path.home()), 'projects',
                                                                                  'python', 'misc', 'sqs_workflow',
                                                                                  'sqs_workflow', 'test_assets',
                                                                                  'test_w_2_panos_without_layout.json'),
            StringConstants.STEPS_KEY: ["ROOM_BOX", "DOOR_DETECTION", "OBJECTS_DETECTION"],
            StringConstants.DOCUMENT_PATH_KEY: "some_document_path_key"
        }

        list_of_messages = self.similarity_processor.start_pre_processing(message_object)

        self.assertTrue(len(list_of_messages) == 7)
        self.assertTrue(json.loads(list_of_messages[0])['fileUrl'].endswith('1m164u2113.JPG'))
        self.assertTrue(json.loads(list_of_messages[0])['messageType'] == 'ROOM_BOX')
        self.assertTrue(json.loads(list_of_messages[1])['fileUrl'].endswith('29utxb8t4f.JPG'))
        self.assertTrue(json.loads(list_of_messages[0])['messageType'] == 'ROOM_BOX')
        self.assertTrue(json.loads(list_of_messages[3])['messageType'] == 'DOOR_DETECTION')
        self.assertTrue(json.loads(list_of_messages[5])['messageType'] == 'OBJECTS_DETECTION')
        self.assertTrue(json.loads(list_of_messages[6])['messageType'] == 'SIMILARITY')

    def test_process_result_files(self):
        # Makes a copy of origin JSON to make changes
        path_to_origin_file = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow',
                                           'sqs_workflow', 'test_assets', 'test_w_2_panos_without_layout.json')
        path_to_copy_origin = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow',
                                           'sqs_workflow', 'tmp', 'test_json_for_test_process_result_files.json')
        shutil.copyfile(path_to_origin_file, path_to_copy_origin)

        document_object = {
            'doc_obj_param_1': 1,
            'doc_obj_param_2': 2,
            'doc_obj_param_3': 'value 3',
        }
        message_object = {
            StringConstants.FLOOR_ID_KEY: 1,
            "fpUrl": "url",
            StringConstants.PANOS_KEY: [
                'pano1', 'pano2'
            ],
            StringConstants.EXECUTABLE_PARAMS_KEY: '--input_path ' + os.path.join(str(Path.home()), 'projects',
                                                                                  'python', 'misc', 'sqs_workflow',
                                                                                  'sqs_workflow', 'tmp',
                                                                                  'test_json_for_test_process_result_files.json'),
            StringConstants.STEPS_KEY: ["ROOM_BOX", "DOOR_DETECTION", "OBJECTS_DETECTION"],
            StringConstants.DOCUMENT_PATH_KEY: "some_document_path_key"
        }

        self.similarity_processor.process_result_files(document_object, message_object)

        # Checks the correctness of the entry
        with open(os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow', 'sqs_workflow', 'tmp',
                               'test_json_for_test_process_result_files.json')) as result_file:
            content = result_file.read()
            self.assertTrue(json.loads(content) == document_object)
            result_file.close()
