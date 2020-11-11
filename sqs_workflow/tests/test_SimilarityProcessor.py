import logging
from unittest import TestCase

from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor
from sqs_workflow.tests.S3HelperMock import S3HelperMock

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class TestSimilarityProcessor(TestCase):

    def test_create_layout_object(self):
        room_box_result = "{\"layout\":{\"z0\":\"0\", \"z1\":\"0\", \"uv\":[[\"0.874929459690343\", \"0.0499472701727508\"], [\"0.6246948329880218\", \"0.836521256741644\"], [\"0.6246948553348896\", \"0.04983696464707826\"], [\"0.8752748643537904\", \"0.8359191738972793\"], [\"0.3744601886079243\", \"0.04994725051497806\"], [\"0.12493895615154749\", \"0.8353210349449639\"], [\"0.12493893386684474\", \"0.05005729692317301\"], [\"0.37411478400664344\", \"0.83591919355491\"]]},\"inference\":{\"inference_id\":\"7394979587235\"}}"
        layout_object = SimilarityProcessor.create_layout_object(StringConstants.ROOM_BOX_KEY, room_box_result)
        self.assertTrue(layout_object[0]['x'] == 134.97460548852348)
        self.assertTrue(layout_object[0]['y'] == -81.00949136890486)
        self.assertTrue(layout_object[0]['type'] == 'corner')
        # todo test door detecting object

    def test_is_similarity_ready(self):
        # Message without 'similarity_document' -> return False
        test_message_1 = {
            "messageType": "SIMILARITY",
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "panos": "pano1"}

        # Message with 'similarity_document' and True in S3HelperMock.is_object_exist -> return True
        test_message_2 = {
            "messageType": "SIMILARITY",
            "orderId": "5da5d5164cedfd0050363a2e",
            "inferenceId": 1111,
            "panos": "pano1",
            "similarity_document": "test-similarity-document/"
        }
        s3_helper_mock = S3HelperMock()
        self.assertFalse(SimilarityProcessor.is_similarity_ready(s3_helper_mock, test_message_1))
        self.assertTrue(SimilarityProcessor.is_similarity_ready(s3_helper_mock, test_message_2))
