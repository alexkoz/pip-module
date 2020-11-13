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
