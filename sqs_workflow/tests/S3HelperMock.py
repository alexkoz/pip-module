import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


class S3HelperMock:
    def __init__(self):
        pass

    def is_object_exist(self, s3_key: str) -> bool:
        logging.info(f'Start checking object: {s3_key}')
        response = {
            "Contents": [{"Key": "test-similarity-document/result.json"}]
        }
        if 'Contents' in response:
            for obj in response['Contents']:
                if s3_key + 'result.json' == obj['Key']:
                    return True
        return False
