import logging
from unittest import TestCase

from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor

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
        # todo get s3 Helper Mock
        s3_helper_mock = None
        message_object = {}
        result = SimilarityProcessor.is_similarity_ready(s3_helper_mock, message_object)
        self.assertTrue(result)
