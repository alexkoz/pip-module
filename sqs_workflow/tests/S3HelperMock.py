import logging

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
import os


class S3HelperMock(S3Helper):

    def __init__(self, existing_keys):
        self.existing_keys = existing_keys
        self.s3_bucket = os.environ['S3_BUCKET']

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

        object_detection_result = '{"layout": [{"id": "indoor_objects_0_g0s6xk4c52", "type": "indoor_object", "class_name": "airplane", "class_id": 3, "score": 0.4678991734981537, "room": "g0s6xk4c52.JPG", "points": [{"x": 44.509755938878754, "y": 12.293173061397567}, {"x": 54.52610857968145, "y": 13.399296945091677}, {"x": 57.45361446281831, "y": 23.402620151789606}, {"x": 43.22499552562945, "y": 19.93411593236044}]}, {"id": "indoor_objects_1_g0s6xk4c52", "type": "indoor_object", "class_name": "bathtub", "class_id": 68, "score": 0.7191537618637085, \"room": "g0s6xk4c52.JPG", "points": [{"x": 74.40805877231611, "y": 18.39319589452269}, {"x": 104.19643404575459, "y": 11.726256335811229}, {"x": 104.22867467122234, "y": 39.32531100406018}, {"x": 69.90404594285616, "y": 55.260041784035025}]}, {"id": "indoor_objects_2_g0s6xk4c52", "type": "indoor_object", "class_name": "bathtub", "class_id": 68, "score": 0.4251323938369751, "room": "g0s6xk4c52.JPG", "points": [{"x": 136.0549254027339, "y": 20.7761003678105}, {"x": 149.2710023617219, "y": 20.234103758363005}, {"x": 149.52577071277187, "y": 41.03230109767824}, {"x": 137.5570963059817, "y": 48.80401816332824}]}, {"id": "indoor_objects_3_g0s6xk4c52", "type": "indoor_object", "class_name": "vent", "class_id": 1163, "score": 0.8348093628883362, "room": "g0s6xk4c52.JPG", "points": [{"x": 154.00083716111988, "y": 43.99838943597399}, {"x": 164.50597531612573, "y": 34.747122051623705}, {"x": 162.90320267734177, "y": 42.52303041652408}, {"x": 154.2021855493312, "y": 51.99604386075782}]}, {"id": "indoor_objects_4_g0s6xk4c52", "type": "indoor_object", "class_name": "tape_(sticky_cloth_or_paper)", "class_id": 1080, "score": 0.6363504528999329, "room": "g0s6xk4c52.JPG", "points": [{"x": -154.47888671786671, "y": 20.41544873109305}, {"x": -152.98291300614875, "y": 20.561932513053534}, {"x": -153.1801421590564, "y": 23.442729603930317}, {"x": -154.78269709765362, "y": 23.824439929516373}]}, {"id": "indoor_objects_5_g0s6xk4c52", "type": "indoor_object", "class_name": "vent", "class_id": 1163, "score": 0.48114752769470215, "room": "g0s6xk4c52.JPG", "points": [{"x": -154.68125707673306, "y": -23.606747744867604}, {"x": -146.8646215464108, "y": -23.019024452129685}, {"x": -147.21385848388684, "y": -21.492998268227524}, {"x": -154.78269709765362, "y": -22.002587790684558}]}, {"id": "indoor_objects_6_g0s6xk4c52", "type": "indoor_object", "class_name": "air_conditioner", "class_id": 2, "score": 0.6033964157104492, "room": "g0s6xk4c52.JPG", "points": [{"x": -116.56666106205446, "y": 8.771525772125614}, {"x": -110.7424232757403, "y": 9.619413976589897}, {"x": -110.85089772726766, "y": 14.700340170245525}, {"x": -116.96249830971085, "y": 13.837256850022968}]}, {"id": "indoor_objects_7_g0s6xk4c52", "type": "indoor_object", "class_name": "curtain", "class_id": 351, "score": 0.42001873254776, "room": "g0s6xk4c52.JPG", "points": [{"x": -136.64347525188776, "y": -4.719383653210258}, {"x": -132.4238506078835, "y": -5.520030116003554}, {"x": -131.67076447930816, "y": 12.095271755915562}, {"x": -135.01629289723417, "y": 12.80002672480937}]}, {"id": "indoor_objects_8_g0s6xk4c52", "type": "indoor_object", "class_name": "vent", "class_id": 1163, "score": 0.7350074052810669, "room": "g0s6xk4c52.JPG", "points": [{"x": -93.42024246247844, "y": 8.29420201575023}, {"x": -87.98241807802509, "y": 8.51658254883884}, {"x": -87.58084981550466, "y": 12.454152352386075}, {"x": -93.2003555201831, "y": 13.036674365761513}]}, {"id": "indoor_objects_9_g0s6xk4c52", "type": "indoor_object", "class_name": "traffic_light", "class_id": 1131, "score": 0.431988000869751, "room": "g0s6xk4c52.JPG", "points": [{"x": -81.86270488800969, "y": -48.268927614931705}, {"x": -58.287076969849494, "y": -52.65027466045524}, {"x": -58.756440657825465, "y": -45.898195277888945}, {"x": -74.39565607249122, "y": -42.854559197891234}]}, {"id": "indoor_objects_10_g0s6xk4c52", "type": "indoor_object", "class_name": "tarp", "class_id": 1083, "score": 0.4116625189781189, "room": "g0s6xk4c52.JPG", "points": [{"x": -81.22126375190712, "y": -4.83183960752649}, {"x": -3.1631910902342497, "y": 12.396741171630126}, {"x": 1.416305434334987, "y": 48.569538035185474}, {"x": -91.8985367216026, "y": 48.08594847575898}]}]}'

        if ProcessingTypesEnum.RoomBox.value in s3_key:
            if 'empty' not in s3_key:
                return roombox_result
            else:
                return ""
        elif ProcessingTypesEnum.DoorDetecting.value in s3_key:
            if 'empty' not in s3_key:
                return door_detection_result
            else:
                return ""
        elif ProcessingTypesEnum.ObjectsDetecting.value in s3_key:
            if 'empty' not in s3_key:
                return object_detection_result
            else:
                return ""

    def save_file_object_on_s3(self, s3_path: str, image_absolute_path: str):
        self.existing_keys.append(s3_path)

    def save_string_object_on_s3(self, s3_key: str, object_body: str, full_url_tag="document", is_public=False) -> str:
        self.existing_keys.append(s3_key)
        return f"https://{os.environ['S3_BUCKET']}.s3-{os.environ['S3_REGION']}.amazonaws.com/{s3_key}"
