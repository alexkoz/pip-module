import os
import sys
from pathlib import Path

from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum


class TestUtils:

    @staticmethod
    def setup_environment_for_unit_tests():
        common_path = os.path.join(str(Path.home()),
                                   'projects',
                                   'python',
                                   'misc',
                                   'sqs_workflow',
                                   'sqs_workflow')
        os.environ['INPUT_DIRECTORY'] = os.path.join(common_path, 'tmp', 'input')
        os.environ['OUTPUT_DIRECTORY'] = os.path.join(common_path, 'tmp', 'output')
        os.environ['S3_BUCKET'] = 'TEST-BUCKET'
        os.environ['S3_REGION'] = 'eu-west-1'
        aids = os.path.join(common_path, 'aids')
        os.environ[f'{ProcessingTypesEnum.Similarity.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.Similarity.value}_SCRIPT'] = os.path.join(aids, 'dummy_similarity.py')
        os.environ[f'{ProcessingTypesEnum.RoomBox.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.RoomBox.value}_SCRIPT'] = os.path.join(aids, 'dummy_roombox.py')
        os.environ[f'{ProcessingTypesEnum.RMatrix.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.RMatrix.value}_SCRIPT'] = os.path.join(aids, 'dummy_rmatrix.py')
        os.environ[f'{ProcessingTypesEnum.DoorDetecting.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.DoorDetecting.value}_SCRIPT'] = os.path.join(aids, 'dummy_dd.py')
        os.environ[f'{ProcessingTypesEnum.Rotate.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.Rotate.value}_SCRIPT'] = os.path.join(aids, 'dummy_rotate.py')
        os.environ[f'{ProcessingTypesEnum.ObjectsDetecting.value}_EXECUTABLE'] = sys.executable
        os.environ[f'{ProcessingTypesEnum.ObjectsDetecting.value}_SCRIPT'] = os.path.join(aids, 'dummy_objects_detection.py')
        os.environ['IMMO_AWS_PROFILE'] = "clipnow"
        os.environ['IMMO_ACCESS'] = "clipnow"
        os.environ['ACCESS'] = "clipnow"
        os.environ['IMMO_SECRET'] = "clipnow"
        os.environ['SECRET'] = "clipnow"
        os.environ['IMMO_REGION_NAME'] = 'eu-west-1'
        os.environ['DOCU_AWS_PROFILE'] = 'sqs'
        os.environ['DOCU_ACCESS'] = 'sqs'
        os.environ['DOCU_SECRET'] = 'sqs'
        os.environ['DOCU_REGION_NAME'] = 'us-east-1'
        os.environ['APP_BRANCH'] = "test"
        os.environ['SLACK_URL'] = "test"
        os.environ['SLACK_ID'] = "test"
        os.environ['GMAIL_USER'] = "test"
        os.environ['GMAIL_PASSW'] = "test"
        os.environ['GMAIL_TO'] = "test"
