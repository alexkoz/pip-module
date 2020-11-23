import logging
from unittest import TestCase
import json
import boto3
import random
import os
import sys

from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor
from sqs_workflow.tests.S3HelperMock import S3HelperMock


class TestSimilarityProcessor(TestCase):
    similarity_processor = SimilarityProcessor()

    def test_create_layout_object(self):
        room_box_result = "{\"layout\":{\"z0\":\"0\", \"z1\":\"0\", \"uv\":[[\"0.874929459690343\", \"0.0499472701727508\"], [\"0.6246948329880218\", \"0.836521256741644\"], [\"0.6246948553348896\", \"0.04983696464707826\"], [\"0.8752748643537904\", \"0.8359191738972793\"], [\"0.3744601886079243\", \"0.04994725051497806\"], [\"0.12493895615154749\", \"0.8353210349449639\"], [\"0.12493893386684474\", \"0.05005729692317301\"], [\"0.37411478400664344\", \"0.83591919355491\"]]},\"inference\":{\"inference_id\":\"7394979587235\"}}"
        layout_object = self.similarity_processor.create_layout_object(StringConstants.ROOM_BOX_KEY, room_box_result)
        self.assertTrue(layout_object[0]['x'] == 134.97460548852348)
        print(json.dumps(layout_object))
        self.assertTrue(layout_object[0]['y'] == -81.00949136890486)
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

    def purge_queue(self, queue_url):
        sqs_client = boto3.client('sqs', region_name='eu-west-2')
        req_purge = sqs_client.purge_queue(QueueUrl=queue_url)
        logging.info(f'Queue is purged')
        return req_purge

    def test_start_pre_processing(self):
        message_object2 = [{'messageType': 'PREPROCESSING', 'orderId': '5da5d5164cedfd0050363a2e', 'inferenceId': 1111, 'floor': 1, 'tourId': '1342386', 'panoUrl': 'urljson', 'documentPath': 'https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json', 'steps': ['ROOM_BOX', 'DOORDETECTION']}, {'createdDate': '16.07.2020 02:26:13', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/8ewi530cga.JPG', 'name': 'Dining room', 'panoId': '5f0f90955e8a061aff256c7a', 'pitch': 0.26, 'roll': -1.26, 'yaw': -8.02, 'inferenceId': 92}, {'createdDate': '16.07.2020 02:26:13', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/8ewi530cga.JPG', 'name': 'Dining room', 'panoId': '5f0f90955e8a061aff256c7a', 'pitch': 0.26, 'roll': -1.26, 'yaw': -8.02, 'inferenceId': 92}, {'createdDate': '16.07.2020 02:26:15', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/fb0cs32y4w.JPG', 'name': 'Laundry area', 'panoId': '5f0f90975e8a061aff256c7d', 'pitch': 0.16, 'roll': -1.17, 'yaw': -2.86, 'inferenceId': 46}, {'createdDate': '16.07.2020 02:26:15', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/fb0cs32y4w.JPG', 'name': 'Laundry area', 'panoId': '5f0f90975e8a061aff256c7d', 'pitch': 0.16, 'roll': -1.17, 'yaw': -2.86, 'inferenceId': 46}, {'createdDate': '16.07.2020 02:26:16', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/2v9r7yijmz.JPG', 'name': 'Bathroom, Master', 'panoId': '5f0f9098734bd35b09a6ac50', 'pitch': 0.02, 'roll': -0.6, 'yaw': -3.31, 'inferenceId': 27}, {'createdDate': '16.07.2020 02:26:16', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/2v9r7yijmz.JPG', 'name': 'Bathroom, Master', 'panoId': '5f0f9098734bd35b09a6ac50', 'pitch': 0.02, 'roll': -0.6, 'yaw': -3.31, 'inferenceId': 27}, {'createdDate': '16.07.2020 02:26:16', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/q3x6i8p2pg.JPG', 'name': 'Bedroom, Master', 'panoId': '5f0f90985e8a061aff256c7e', 'pitch': -0.22, 'roll': -0.75, 'yaw': -4.11, 'inferenceId': 67}, {'createdDate': '16.07.2020 02:26:16', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/q3x6i8p2pg.JPG', 'name': 'Bedroom, Master', 'panoId': '5f0f90985e8a061aff256c7e', 'pitch': -0.22, 'roll': -0.75, 'yaw': -4.11, 'inferenceId': 67}, {'createdDate': '16.07.2020 02:26:17', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/61d2190xi5.JPG', 'name': 'Living Room', 'panoId': '5f0f90995e8a061aff256c7f', 'pitch': 0.67, 'roll': -1.19, 'yaw': -6.84, 'inferenceId': 36}, {'createdDate': '16.07.2020 02:26:17', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/61d2190xi5.JPG', 'name': 'Living Room', 'panoId': '5f0f90995e8a061aff256c7f', 'pitch': 0.67, 'roll': -1.19, 'yaw': -6.84, 'inferenceId': 36}, {'createdDate': '16.07.2020 02:26:19', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/9kt93s3pk8.JPG', 'name': 'Bathroom, Half', 'panoId': '5f0f909b734bd35b09a6ac52', 'pitch': 0.68, 'roll': -1.81, 'yaw': -2.86, 'inferenceId': 3}, {'createdDate': '16.07.2020 02:26:19', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/9kt93s3pk8.JPG', 'name': 'Bathroom, Half', 'panoId': '5f0f909b734bd35b09a6ac52', 'pitch': 0.68, 'roll': -1.81, 'yaw': -2.86, 'inferenceId': 3}, {'createdDate': '16.07.2020 02:26:22', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/54kbn8dnx4.JPG', 'name': 'Garage', 'panoId': '5f0f909e734bd35b09a6ac55', 'pitch': 1.09, 'roll': -1.53, 'yaw': 2.41, 'inferenceId': 69}, {'createdDate': '16.07.2020 02:26:22', 'fileUrl': 'https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/original-images/54kbn8dnx4.JPG', 'name': 'Garage', 'panoId': '5f0f909e734bd35b09a6ac55', 'pitch': 1.09, 'roll': -1.53, 'yaw': 2.41, 'inferenceId': 69}]
        self.purge_queue(os.environ['QUEUE_LINK'])

        list_json_messages = self.similarity_processor.start_pre_processing(message_object2, os.environ['INPUT_DIRECTORY'])
        for json_message in list_json_messages:
            message_object = json.loads(json_message)
            if message_object['messageType'] == 'SIMILARITY':
                self.assertTrue(message_object['panos'])
                for pano in message_object['panos']:
                    self.assertTrue(pano['fileUrl'])
            else:
                self.assertTrue(message_object['messageType'] == StringConstants.DOOR_DETECTION_KEY
                                or message_object['messageType'] == StringConstants.ROOM_BOX_KEY
                                or message_object['messageType'] == StringConstants.R_MATRIX_KEY)

        # todo define input dir
        # todo read json from input dir
        # todo get all panos out of
        # todo send individual messages according to steps
        # todo send main similarity message

        # todo wait till processed
        print("All Done")

