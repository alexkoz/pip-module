import json
from unittest import TestCase
from os.path import dirname

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.tests.S3HelperMock import S3HelperMock
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor
from sqs_workflow.aws.s3.S3Helper import S3Helper
import logging


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class TestSimilarityProcessor(TestCase):
    similarity_processor = SimilarityProcessor()

    def test_create_layout_object(self):
        room_box_result = '{"z0": "0", "z1": "0", "uv": [[0.8942103326473919, 0.3353772676236854], [0.5747235927670448, 0.6223832045044406], [0.575059459160671, 0.37344853854460625], [0.8946108521103336, 0.6597705138137632], [0.4391388923396096, 0.3687213328274126], [0.08800329189223322, 0.6700959772611611], [0.08779664823660581, 0.3244858638081926], [0.4389803229974563, 0.6268292928215364]]}'
        layout_object = self.similarity_processor.create_layout_object(ProcessingTypesEnum.RoomBox.value,
                                                                       room_box_result)
        layout_object = json.loads(layout_object)
        self.assertTrue(layout_object[0]['x'] == 141.9157197530611)

        self.assertTrue(layout_object[0]['y'] == -29.632091827736627)
        self.assertTrue(layout_object[0]['type'] == 'corner')
        # todo test door detecting object

    def test_assemble_results_into_document(self):
        s3_helper_mock = S3HelperMock([])
        message_object = {
            "floor": 1,
            "fpUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/map-images/1-floor-5i2cvu550f.jpg",
            "panos": [
                {"createdDate": "16.07.2020 02:26:13",
                 "fileUrl": "http://domen.com/img1.JPG"},
                {"createdDate": "18.07.2020 02:43:15",
                 "fileUrl": "http://domen.com/img2.JPG"}
            ]
        }
        list_result = ['api/inference/ROOM_BOX/1111/img1.JPG/result.json',
                       'api/inference/ROOM_BOX/1111/img2.JPG/result.json',
                       'api/inference/DOOR_DETECTION/1111/img1.JPG/result.json',
                       'api/inference/DOOR_DETECTION/1111/img2.JPG/result.json']
        new_message_object = SimilarityProcessor.assemble_results_into_document(s3_helper_mock, message_object,
                                                                                list_result)
        self.assertEqual(new_message_object['panos'][0]['fileUrl'], "http://domen.com/img1.JPG")
        self.assertEqual(new_message_object['panos'][1]['layout'][0]['type'], 'corner')
        self.assertEqual(new_message_object['panos'][1]['layout'][8]['id'], 'door_108')

    def test_start_pre_processing(self):
        sqs_processor = SqsProcessor('-immoviewer-ai')
        preprocessing_message = {
            "messageType": ProcessingTypesEnum.Preprocessing.value,
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "floor": 1,
            "tourId": "1342386",
            "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
            "steps": [ProcessingTypesEnum.RoomBox.value, ProcessingTypesEnum.DoorDetecting.value]
        }
        json_message_object = sqs_processor.prepare_for_processing(json.dumps(preprocessing_message))
        similarity_message = json.loads(json_message_object)
        file_path = similarity_message[StringConstants.EXECUTABLE_PARAMS_KEY].replace('--input_path', '') \
            .split()[0].strip()

        with open(file_path) as f:
            json_message_object = json.load(f)

        list_json_messages = self.similarity_processor.start_pre_processing(similarity_message)
        self.assertTrue(
            len(list_json_messages) == (len(preprocessing_message[StringConstants.STEPS_KEY]) * len(
                json_message_object[StringConstants.PANOS_KEY]) + 1))
        for json_message in list_json_messages:
            message_object = json.loads(json_message)
            if message_object['messageType'] == ProcessingTypesEnum.Similarity.value:
                self.assertTrue(len(message_object[StringConstants.STEPS_KEY]) == 2)
                self.assertTrue(StringConstants.DOCUMENT_PATH_KEY not in message_object)
            else:
                self.assertTrue(message_object['messageType'] == ProcessingTypesEnum.DoorDetecting.value
                                or message_object['messageType'] == ProcessingTypesEnum.RoomBox.value)

    def test_is_similarity_ready(self):
        similarity_message_w_document_path = {
            "messageType": "SIMILARITY",
            "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
            "tourId": "5fa1df49014bf357cf250d52",
            "panoId": "5fa1df55014bf357cf250d64"
        }
        res = self.similarity_processor.is_similarity_ready(S3Helper(), similarity_message_w_document_path)
        self.assertTrue(len(res['panos']) == 23)

        similarity_message_w_steps_document_path = {
            "messageType": "SIMILARITY",
            "stepsDocumentPath": "file:///Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/test.json",
            "tourId": "5fa1df49014bf357cf250d52",
            "inferenceId": 100,
            "panoId": "5fa1df55014bf357cf250d64",
            "steps": ['ROOM_BOX', 'SIMILARITY'],
            "panos": "pano1",
            "executable_params": "--input_path /Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/tmp/input/ad7ede0d6d45f7dc4656763b87b81db2/order_1012550_floor_1.json.json --output_path /Users/alexkoz/projects/python/misc/sqs_workflow/sqs_workflow/tmp/output/"
        }

        res2 = self.similarity_processor.is_similarity_ready(S3Helper(), similarity_message_w_steps_document_path)
        self.assertTrue(res2['panos'][0]['layout'])

        # Checks that input file modified
        input_path = similarity_message_w_steps_document_path['executable_params'].split(' ')[1]
        with open(input_path) as f:
            modified_json_contains = json.load(f)
        self.assertTrue(modified_json_contains['panos'][0]['layout'])
