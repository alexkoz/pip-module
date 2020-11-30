import logging
import os
from pathlib import Path

from unittest import TestCase

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.tests.test_sqsProcessor import TestSqsProcessor


class TestS3Helper(TestCase):
    s3_helper = S3Helper()

    def test_save_file_object_on_s3(self):
        TestSqsProcessor.clear_directory('api/inference/test-save-on-s3')
        logging.info('Cleared S3 key folder on S3')

        test_absolute_path = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow',
                                          'sqs_workflow', 'tmp') + '/tempfile.json'
        open(test_absolute_path, 'w').write('{}')
        logging.info('Created temporary json file for uploading to S3')

        test_s3_key = os.path.join('api', 'inference', 'test-save-on-s3') + '/tempfile.json'
        self.s3_helper.save_file_object_on_s3(test_s3_key, test_absolute_path)

        self.assertTrue(self.s3_helper.is_object_exist(test_s3_key))

    def test_download_file_object_from_s3(self):
        # Upload file to S3
        TestSqsProcessor.clear_directory('api/inference/test-download-from-s3')
        logging.info('Cleared S3 key folder on S3')

        test_absolute_path = os.path.join(str(Path.home()), 'projects', 'python', 'misc', 'sqs_workflow',
                                          'sqs_workflow', 'tmp') + '/tempfile_download.json'
        open(test_absolute_path, 'w').write('{}')
        logging.info('Created temporary json file for uploading to S3')

        test_s3_key = os.path.join('api', 'inference', 'test-dowload-from-s3') + '/tempfile_download.json'
        self.s3_helper.save_file_object_on_s3(test_s3_key, test_absolute_path)

        # Deleted created temporary file locally. Still on S3
        os.remove(test_absolute_path)

        self.s3_helper.download_file_object_from_s3(test_s3_key, test_absolute_path)
        self.assertTrue(os.path.isfile(test_absolute_path))
