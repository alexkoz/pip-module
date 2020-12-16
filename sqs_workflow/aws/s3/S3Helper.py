import logging
import os
from sqs_workflow.utils.StringConstants import StringConstants

import boto3


class S3Helper:
    s3_bucket = os.environ['S3_BUCKET']
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ['IMMO_ACCESS'],
        aws_secret_access_key=os.environ['IMMO_SECRET'],
        region_name=os.environ['S3_REGION']
    )

    def __init__(self):
        assert self.s3_bucket
        assert self.s3_client
        pass

    def is_object_exist(self, s3_key: str) -> bool:
        logging.info(f'Start checking object: {s3_key}')
        response = self.s3_client.list_objects_v2(Bucket=self.s3_bucket, Prefix=s3_key, Delimiter='/')
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'] == s3_key:
                    return True
        return False

    def save_string_object_on_s3(self, s3_key: str,
                                 object_body: str,
                                 full_url_tag="document",
                                 is_public=False) -> str:
        logging.info(f'Start saving object: {s3_key}')

        session = boto3.Session(
            aws_access_key_id=os.environ['ACCESS'],
            aws_secret_access_key=os.environ['SECRET']
        )
        s3 = session.resource('s3')
        obj = s3.Object(self.s3_bucket, s3_key)
        full_url_tag = f'{StringConstants.FILE_URL_KEY}={full_url_tag}'
        logging.info(f"Tag for object:{full_url_tag}")
        obj.put(Body=object_body,
                Tagging=full_url_tag)
        if is_public:
            object_acl = s3.ObjectAcl(self.s3_bucket, s3_key)
            object_acl.put(ACL='public-read')
            logging.info(f'Public access to key:{s3_key}')
        object_url = f"https://{self.s3_bucket}.s3-{os.environ['S3_REGION']}.amazonaws.com/{s3_key}"
        logging.info(f'Uploaded new file: {s3_key} to s3 with url:{object_url}')
        return object_url

    def save_file_object_on_s3(self,
                               s3_key: str,
                               file_absolute_path: str):
        logging.info(f'Start saving s3 object:{s3_key} file:{file_absolute_path}')

        self.s3_client.upload_file(file_absolute_path,
                                   self.s3_bucket,
                                   s3_key)
        logging.info(f'Uploaded new file: {s3_key} to s3')

    def download_file_object_from_s3(self,
                                     s3_key: str,
                                     file_absolute_path: str):
        logging.info(f'Start saving s3 object:{s3_key} file:{file_absolute_path}')

        with open(file_absolute_path, 'wb') as local_file:
            self.s3_client.download_fileobj(self.s3_bucket, s3_key, local_file)
            local_file.close()
        logging.info(f'Uploaded new file: {s3_key} to s3')

    def read_s3_object(self, s3_key) -> str:
        logging.info(f'Start reading s3 file:{s3_key}')
        data = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
        file_content_from_s3 = data['Body'].read().decode('utf-8')
        logging.info(f'S3 file:{s3_key} has body:{file_content_from_s3}')
        return file_content_from_s3

    def list_s3_objects(self, prefix: str):
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
        list_of_objects = []
        logging.info('list of objects: ', list_of_objects)
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    list_of_objects.append(obj['Key'])
                    logging.info(f'Added object {obj["Key"]} to list of objects')
        return list_of_objects

    def count_files_s3(self, s3_key: str) -> list:
        logging.info(f'Start count objects in: {s3_key}')
        response = self.s3_client.list_objects_v2(Bucket=self.s3_bucket, Prefix=s3_key)
        if 'Contents' in response:
            array_of_result_json = []
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('result.json'):
                    array_of_result_json.append(key)
            return array_of_result_json

    def is_processing_complete(self, prefix: str, num_of_expected_results: int) -> bool:
        list_of_objects = self.list_s3_objects(prefix)
        logging.info(f'Len of s3_objects_list w/ prefix: {prefix} =', len(list_of_objects))
        return len(list_of_objects) == num_of_expected_results
