import logging
from unittest import TestCase
import json

from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor
from sqs_workflow.tests.S3HelperMock import S3HelperMock

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


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

    def test_is_similarity_ready(self):
        # Message without 'similarity_document' -> return False
        test_message_1 = {
            "messageType": "SIMILARITY",
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
            "steps": ['ROOMBOX'],
            "panos": "pano1"}

        # Message with 'similarity_document' and True in S3HelperMock.is_object_exist -> return True
        test_message_2 = {
            "messageType": "SIMILARITY",
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "documentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
            "steps": ['ROOMBOX'],
            "panos": "pano1",
        }

        test_message_3 = {
            "messageType": "SIMILARITY",
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "panos": "pano1",
        }
        s3_helper_mock = S3HelperMock([])

        json_message = '{"floor": 1, "fpUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/map-images/1-floor-5ucnzloa3i.jpg", "panos": [{"createdDate": "01.06.2020 14:56:41", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/di7z4k5425.JPG", "name": "Main Entry", "panoId": "5ed4ecf9eac0e75ce1884a0e", "pitch": -0.46, "roll": 0.05, "yaw": 1.77}, {"createdDate": "01.06.2020 14:56:41", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/f63ubad57u.JPG", "name": "Kitchen", "panoId": "5ed4ecf9e9ecff21cfd718c0", "pitch": -0.55, "roll": -0.21, "yaw": -2.58}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/d5r69z203i.JPG", "name": "Kitchen 2", "panoId": "5ed4ecfaeac0e75ce1884a0f", "parentPanoId": "5ed4ecf9e9ecff21cfd718c0", "pitch": -1.35, "roll": -0.35, "yaw": 40.91}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/18zg9872p3.JPG", "name": "Dining room", "panoId": "5ed4ecfae9ecff21cfd718c1", "pitch": -0.71, "roll": 0.15, "yaw": 1.65}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/xo5sk2d6hz.JPG", "name": "Dining room 2", "panoId": "5ed4ecfaeac0e75ce1884a10", "parentPanoId": "5ed4ecfae9ecff21cfd718c1", "pitch": -0.2, "roll": -0.22, "yaw": 39.15}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/x3845c7hrl.JPG", "name": "Living Room", "panoId": "5ed4ecfae9ecff21cfd718c2", "pitch": -0.36, "roll": 0.02, "yaw": 32.58}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/2sc86kpj70.JPG", "name": "Living Room 2", "panoId": "5ed4ecfaeac0e75ce1884a11", "parentPanoId": "5ed4ecfae9ecff21cfd718c2", "pitch": -1.04, "roll": -0.02, "yaw": 3.41}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/1m164u2113.JPG", "name": "Hallway", "panoId": "5ed4ecfae9ecff21cfd718c3", "pitch": -0.94, "roll": 0.25, "yaw": -5.71}, {"createdDate": "01.06.2020 14:56:42", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/82o0j5993l.JPG", "name": "Hallway 2", "panoId": "5ed4ecfaeac0e75ce1884a12", "parentPanoId": "5ed4ecfae9ecff21cfd718c3", "pitch": -0.64, "roll": -0.14, "yaw": -0.49}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/hlx6x4x99m.JPG", "name": "Hallway 3", "panoId": "5ed4ecfbe9ecff21cfd718c4", "parentPanoId": "5ed4ecfae9ecff21cfd718c3", "pitch": -0.55, "roll": -0.34, "yaw": -4.42}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/ty0gnunjjm.JPG", "name": "Hallway Bathroom", "panoId": "5ed4ecfbeac0e75ce1884a13", "pitch": 0.29, "roll": 0.52, "yaw": -3.76}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/kzqjysjh46.JPG", "name": "Hallway Bathroom 2", "panoId": "5ed4ecfbe9ecff21cfd718c5", "parentPanoId": "5ed4ecfbeac0e75ce1884a13", "pitch": -0.14, "roll": -0.13, "yaw": -28.06}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/n0l066b0r4.JPG", "name": "Small Bedroom", "panoId": "5ed4ecfbeac0e75ce1884a14", "pitch": -0.56, "roll": -1.05, "yaw": -43.65}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/ecxa55y03b.JPG", "name": "Small Bedroom 2", "panoId": "5ed4ecfbe9ecff21cfd718c6", "parentPanoId": "5ed4ecfbeac0e75ce1884a14", "pitch": -0.87, "roll": 0.39, "yaw": 37.28}, {"createdDate": "01.06.2020 14:56:43", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/7896e3650n.JPG", "name": "Master Bedroom", "panoId": "5ed4ecfbeac0e75ce1884a15", "pitch": -0.47, "roll": -0.69, "yaw": -38.12}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/8r9j66v11x.JPG", "name": "Master Bedroom 2", "panoId": "5ed4ecfce9ecff21cfd718c7", "parentPanoId": "5ed4ecfbeac0e75ce1884a15", "pitch": -0.69, "roll": 0.14, "yaw": 37.28}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/h23me8r766.JPG", "name": "Bedroom ", "panoId": "5ed4ecfceac0e75ce1884a16", "pitch": -0.44, "roll": -1.19, "yaw": 30.04}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/29utxb8t4f.JPG", "name": "Bedroom  2", "panoId": "5ed4ecfce9ecff21cfd718c8", "parentPanoId": "5ed4ecfceac0e75ce1884a16", "pitch": -0.32, "roll": -0.57, "yaw": 34.96}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/305d183xh5.JPG", "name": "Bathroom", "panoId": "5ed4ecfceac0e75ce1884a17", "pitch": -0.77, "roll": -0.46, "yaw": -8.41}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/s2gn1ls870.JPG", "name": "Bathroom 2", "panoId": "5ed4ecfce9ecff21cfd718c9", "parentPanoId": "5ed4ecfceac0e75ce1884a17", "pitch": -0.64, "roll": -0.16, "yaw": -13.71}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/b7wk34u101.JPG", "name": "Kitchen 3", "panoId": "5ed4ecfceac0e75ce1884a18", "parentPanoId": "5ed4ecf9e9ecff21cfd718c0", "pitch": -1.07, "roll": -0.72, "yaw": 7.26}, {"createdDate": "01.06.2020 14:56:44", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/jth5z9w0up.JPG", "name": "Attached Garage", "panoId": "5ed4ecfce9ecff21cfd718ca", "pitch": -1.1, "roll": -0.08, "yaw": 12.77}, {"createdDate": "01.06.2020 14:56:45", "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/u5li5808v8/5ed4ecf7e9ecff21cfd718b8/Tour/original-images/bk9ud1320w.JPG", "name": "Attached Garage 2", "panoId": "5ed4ecfdeac0e75ce1884a19", "parentPanoId": "5ed4ecfce9ecff21cfd718ca", "pitch": -0.7, "roll": 0.24, "yaw": -2.66}], "tourId": "1334373", "tourLink": "https://app.docusketch.com/admin/tour/5ed4ecf7e9ecff21cfd718b7?accessKey=5e8b&p.device=Desktop&orderId=5ed4edefe9ecff21cfd718d1&dollhousePreview=1"}'

        # todo finish test cases
        # self.assertEqual(self.similarity_processor.is_similarity_ready(s3_helper_mock, test_message_2), json_message)
        self.similarity_processor.is_similarity_ready(s3_helper_mock, test_message_1)

    def test_assemble_results_into_document(self):
        s3_helper_mock = S3HelperMock([])
        message_object = {
            "floor": 1,
            "fpUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/76fu441i6j/5f0f90925e8a061aff256c76/Tour/map-images/1-floor-5i2cvu550f.jpg",
            "panos": [
                {"createdDate": "16.07.2020 02:26:13",
                 "fileUrl": "http://domen.com/img1.JPG"},
                {"createdDate": "18.07.2020 02:43:15",
                 "fileUrl": "http://domen.com/img2.JPG"},
                {"createdDate": "20.07.2020 04:51:23",
                 "fileUrl": "http://domen.com/img3.JPG"},
                {"createdDate": "21.07.2020 11:07:63",
                 "fileUrl": "http://domen.com/img4.JPG"}
            ]
        }
        list_result = ['api/inference/ROOM_BOX/1111/img1.JPG/result.json',
                       'api/inference/ROOM_BOX/1111/img2.JPG/result.json',
                       'api/inference/DOOR_DETECTION/2222/img3.JPG/result.json',
                       'api/inference/DOOR_DETECTION/2222/img4.JPG/result.json']
        new_message_object = SimilarityProcessor.assemble_results_into_document(s3_helper_mock, message_object,
                                                                                list_result)
        self.assertEqual(new_message_object['panos'][0]['fileUrl'], "http://domen.com/img1.JPG")
        self.assertEqual(new_message_object['panos'][1]['fileUrl'], "http://domen.com/img2.JPG")
        self.assertEqual(new_message_object['panos'][2]['layout'][0]['id'], 'door_108')
