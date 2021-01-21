import logging
import os
import shutil
import time
from pathlib import Path
from unittest import TestCase

from sqs_workflow.aws.s3.S3Helper import S3Helper


class TestS3Helper(TestCase):
    common_path = os.path.join(str(Path.home()),
                               'projects',
                               'python',
                               'misc',
                               'sqs_workflow',
                               'sqs_workflow')

    def setUp(self) -> None:
        self.s3_helper = S3Helper()
        self.clear_local_directories()

    def tearDown(self) -> None:
        self.clear_local_directories()

    @staticmethod
    def clear_local_directories():
        if os.path.isdir(os.path.join(TestS3Helper.common_path, 'tmp', 'input')):
            shutil.rmtree(os.path.join(TestS3Helper.common_path, 'tmp', 'input'))
            shutil.rmtree(os.path.join(TestS3Helper.common_path, 'tmp', 'output'))
            logging.info('Deleted all files from i/o directories')

    def test_save_file_object_on_s3(self):
        def save_file_object_on_s3_mock(test_s3_key, test_absolute_path):
            shutil.copyfile(test_absolute_path, test_s3_key)

        def is_object_exist_mock(test_s3_key):
            return os.path.exists(test_s3_key)

        self.s3_helper.save_file_object_on_s3 = save_file_object_on_s3_mock
        self.s3_helper.is_object_exist = is_object_exist_mock

        logging.info('Cleared S3 key folder on S3')

        test_absolute_path = os.path.join(self.common_path, 'test_assets', 'tempfile.json')
        with open(test_absolute_path, 'w') as write_file:
            write_file.write('{}')
            write_file.close()
        logging.info('Created temporary json file for uploading to S3')

        test_s3_key = os.path.join(self.common_path, 'tmp', 'input', 'test-save-on-s3', 'tempfile.json')

        os.makedirs(os.path.join(self.common_path, 'tmp', 'input', 'test-save-on-s3'))
        os.makedirs(os.path.join(self.common_path, 'tmp', 'output', 'test-save-on-s3'))

        self.s3_helper.save_file_object_on_s3(test_s3_key, test_absolute_path)
        self.assertTrue(self.s3_helper.is_object_exist(test_s3_key))

    def test_sync_dir_s3(self):
        def save_file_object_on_s3_mock(test_s3_key, test_absolute_path):
            s3_key = os.path.join(os.environ['HOME'], test_s3_key)
            shutil.copyfile(test_absolute_path, s3_key)

        def is_object_exist_mock(test_s3_key):
            return os.path.exists(test_s3_key)

        self.s3_helper.save_file_object_on_s3 = save_file_object_on_s3_mock
        self.s3_helper.is_object_exist = is_object_exist_mock
        test_s3_keys = []
        logging.info('Cleared S3 key folder on S3')
        timestamp = str(time.time())
        input_path = os.path.join(self.common_path,'tmp', timestamp, 'test_assets')
        output_path = os.path.join(self.common_path, 'tmp', timestamp, 'output', 'test-save-on-s3')
        os.makedirs(input_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        for index in range(5):
            test_absolute_path = os.path.join(input_path, f'tempfile_{index}.json')
            with open(test_absolute_path, 'w') as write_file:
                write_file.write('{}')
                write_file.close()
            logging.info('Created temporary json file for uploading to S3')
            test_s3_keys.append(os.path.join(input_path, f'tempfile_{index}.json'))

        self.s3_helper.sync_directory_with_s3(input_path, output_path)
        for index in range(5):
            self.assertTrue(self.s3_helper.is_object_exist(test_s3_keys[index]))

    def test_download_file_object_from_s3(self):
        def save_file_object_on_s3_mock(test_s3_key, test_absolute_path):
            shutil.copyfile(test_absolute_path, test_s3_key)

        def download_file_object_from_s3_mock(test_s3_key, test_absolute_path):
            shutil.copyfile(test_s3_key, test_absolute_path)

        self.s3_helper.save_file_object_on_s3 = save_file_object_on_s3_mock
        self.s3_helper.download_file_object_from_s3 = download_file_object_from_s3_mock

        # Upload file to S3
        logging.info('Cleared S3 key folder on S3')

        test_absolute_path = os.path.join(self.common_path, 'test_assets', 'tempfile_download.json')
        with open(test_absolute_path, 'w') as write_file:
            write_file.write('{}')
            write_file.close()
        logging.info('Created temporary json file for uploading to S3')

        test_s3_key = os.path.join(self.common_path, 'tmp', 'input', 'test-save-on-s3', 'tempfile_download.json')

        os.makedirs(os.path.join(self.common_path, 'tmp', 'input', 'test-save-on-s3'))
        os.makedirs(os.path.join(self.common_path, 'tmp', 'output', 'test-save-on-s3'))

        self.s3_helper.save_file_object_on_s3(test_s3_key, test_absolute_path)

        # Deleted created temporary file locally. Still on S3
        os.remove(test_absolute_path)

        self.s3_helper.download_file_object_from_s3(test_s3_key, test_absolute_path)
        self.assertTrue(os.path.isfile(test_absolute_path))
