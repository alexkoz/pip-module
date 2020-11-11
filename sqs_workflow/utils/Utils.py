import json
import botocore

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor


class Utils:
    processor = SqsProcessor()
    s3_helper = S3Helper()

    def __init__(self):
        pass

    def download_from_http(self, key):
        path_to_json_locally = '/Users/alexkoz/projects/sqs_workflow/sqs_workflow/tmp/tmp_json/' + key
        try:
            self.s3_helper.s3_bucket.download_file(key, path_to_json_locally)
            with open(path_to_json_locally) as json_file:
                data = json.load(json_file)
                return data
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise
