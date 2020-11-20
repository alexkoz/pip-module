from unittest import TestCase
from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.Utils import Utils
import os


class TestS3(TestCase):
    def clear_directory(self, path_to_folder_in_bucket: str):
        sync_command = f"aws s3 --profile {os.environ['AWS_PROFILE']} rm s3://{os.environ['S3_BUCKET']}/{path_to_folder_in_bucket} --recursive"
        print(sync_command)
        stream = os.popen(sync_command)
        output = stream.read()
        print(output)

    def test_e2e_s3(self):
        s3_helper = S3Helper()
        self.clear_directory('api/inference/test_type/test_inference/')
        processor = SqsProcessor()

        message_type = 'test_type'
        inference_id = 'test_inference'
        file_url = "http://s3.com/dir/image.jpg"
        s3_key = Utils.create_result_s3_key('api/inference/',
                                            message_type,
                                            inference_id,
                                            'image_id',
                                            StringConstants.RESULT_FILE_NAME)
        for i in range(5):
            name = s3_key + '-file_' + str(i) + '.json'
            content = 'some-body-content-' + str(i)
            s3_helper.save_object_on_s3(name, content, file_url)

        self.assertTrue(s3_helper.is_processing_complete('api/inference/test_type/test_inference', 5))
        self.assertTrue(not s3_helper.is_processing_complete('api/inference/test_type/test_inference', 10))
