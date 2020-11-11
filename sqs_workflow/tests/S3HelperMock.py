import logging
from sqs_workflow.aws.s3.S3Helper import S3Helper

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class S3HelperMock(S3Helper):

    def __init__(self, existing_keys):
        self.existing_keys = existing_keys

    def is_object_exist(self, s3_key: str) -> bool:
        logging.info(f'Start checking object: {s3_key}')
        #todo check if key is in existing keys
        response = {
            "Contents": [{"Key": "test-similarity-document/result.json"}]
        }
        if 'Contents' in response:
            for obj in response['Contents']:
                if s3_key + 'result.json' == obj['Key']:
                    return True
        return False
