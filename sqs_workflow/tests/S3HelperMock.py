import logging

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum


class S3HelperMock(S3Helper):

    def __init__(self, existing_keys):
        self.existing_keys = existing_keys

    def is_object_exist(self, s3_key: str) -> bool:
        logging.info(f'Start checking object: {s3_key}')
        response = {
            "Contents": [{"Key1": "api/inference/ROOM_BOX/100/di7z4k5425.JPG/result.json",
                          "Key2": "api/inference/DOOR_DETECTION/100/di7z4k5425.JPG/result.json",
                          "Key3": "api/inference/ROOM_BOX/100/f63ubad57u.JPG/result.json",
                          "Key4": "api/inference/DOOR_DETECTION/100/f63ubad57u.JPG/result.json"
                          }]
        }
        if 'Contents' in response:
            for obj in response['Contents']:
                if s3_key in obj.values():
                    return True
        return False

    def read_s3_object(self, s3_key) -> str:
        roombox_result = '{"layout": [{"x": 134.97460548852348, "y": -81.00949136890486, "type": "corner"}, {"x": 44.89013987568783, "y": 60.57382621349592, "type": "corner"}, {"x": 44.89014792056024, "y": -81.02934636352592, "type": "corner"}, {"x": 135.09895116736456, "y": 60.46545130151028, "type": "corner"}, {"x": -45.19433210114725, "y": -81.00949490730395, "type": "corner"}, {"x": -135.02197578544292, "y": 60.3577862900935, "type": "corner"}, {"x": -135.0219838079359, "y": -80.98968655382886, "type": "corner"}, {"x": -45.31867775760836, "y": 60.46545483988379, "type": "corner"}]}'
        door_detection_result = '{"layout": [{"color": 16777215, "computedValues": {"width": 71.97554911272209}, "doorDirectionRight": true, "doorType": 1, "elementId": "beta", "id": "door_108", "pathCorner": 1, "pathDirection": 1, "points": [{"x": 35.80435909946351,"y": -17.074991679581473},{"x": 44.21902962059778,"y": -20.455211700643225},{"x": 44.21902962059778,"y": 29.503975135145815},{"x": 35.80435923214196,"y": 24.985153472533955}],"positionOffset": 0,"room": "54kbn8dnx4.JPG","rotationOffset": 0,"text": "Door","type": "door", "zOrder": 3}, \
                                 {"color": 16777215, "computedValues": {"width": 71.97554911272209}, "doorDirectionRight": true, "doorType": 1, "elementId": "beta", "id": "door_110", "pathCorner": 1, "pathDirection": 1, "points": [{"x": 35.80435909946351,"y": -17.074991679581473},{"x": 44.21902962059778,"y": -20.455211700643225},{"x": 44.21902962059778,"y": 29.503975135145815},{"x": 35.80435923214196,"y": 24.985153472533955}],"positionOffset": 0,"room": "54kbn8dnx4.JPG","rotationOffset": 0,"text": "Door","type": "door", "zOrder": 3}]}'
        if ProcessingTypesEnum.RoomBox.value in s3_key:
            return roombox_result
        elif ProcessingTypesEnum.DoorDetecting.value in s3_key:
            if 'empty' not in s3_key:
                return door_detection_result
            else:
                return ""
