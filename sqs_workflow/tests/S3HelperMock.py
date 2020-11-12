import logging
from sqs_workflow.aws.s3.S3Helper import S3Helper

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class S3HelperMock(S3Helper):

    def __init__(self, existing_keys):
        self.existing_keys = existing_keys

    def is_object_exist(self, s3_key: str) -> bool:
        logging.info(f'Start checking object: {s3_key}')
        response = {
            "Contents": [{"Key": "api/inference/ROOMBOX/1111/di7z4k5425.JPG/result.json"}]
        }
        if 'Contents' in response:
            for obj in response['Contents']:
                if s3_key == obj['Key']:
                    return True
        return False

    def read_s3_object(self, s3_key) -> str:
        roombox_result = '[{"x": 134.97460548852348, "y": -81.00949136890486, "type": "corner"}, {"x": 44.89013987568783, "y": 60.57382621349592, "type": "corner"}, {"x": 44.89014792056024, "y": -81.02934636352592, "type": "corner"}, {"x": 135.09895116736456, "y": 60.46545130151028, "type": "corner"}, {"x": -45.19433210114725, "y": -81.00949490730395, "type": "corner"}, {"x": -135.02197578544292, "y": 60.3577862900935, "type": "corner"}, {"x": -135.0219838079359, "y": -80.98968655382886, "type": "corner"}, {"x": -45.31867775760836, "y": 60.46545483988379, "type": "corner"}]'
        return roombox_result
