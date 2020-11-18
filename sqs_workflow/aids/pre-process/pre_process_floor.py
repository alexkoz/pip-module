import os
import boto3
import logging
import json
from pathlib import Path


def cleaning_json(path_to_json, filename):
    with open(path_to_json) as json_file:
        data = json.load(json_file)
        for pano in data['panos']:
            del pano['layout']
        logging.info('finish delete layouts')

        path_to_save_edited = os.path.join(str(Path.home()), 'projects', 'sqs_workflow', 'sqs_workflow', 'tmp',
                                           'edited') + filename
        with open(path_to_save_edited, 'w') as outfile:
            json.dump(data, outfile)
        logging.info(f'Saved {filename} in edited folder')


def sync_local_s3(local_path, s3_directory):
    sync_command = 'aws --profile ' + os.environ['AWS_PROFILE'] + ' s3 sync ' + local_path + ' ' + s3_directory
    print(sync_command)
    stream = os.popen(sync_command)
    output = stream.read()
    print(output)


s3 = boto3.resource('s3')
s3_bucket = s3.Bucket(os.environ['S3_BUCKET'])

for s3_object in s3_bucket.objects.filter(Prefix='storage/segmentation/pretty-floors_data_from_01.06.2020/'):
    path, filename = os.path.split(s3_object.key)
    logging.info(f'Downloads file {filename}')
    path_to_save_file = os.path.join(str(Path.home()), 'projects', 'sqs_workflow', 'sqs_workflow', 'tmp',
                                     'origins') + '/' + filename
    s3_bucket.download_file(s3_object.key, path_to_save_file)
    cleaning_json(path_to_save_file, filename)

local_path = os.path.join(str(Path.home()), 'projects', 'sqs_workflow', 'sqs_workflow', 'tmp', 'edited')
s3_path = 's3://' + os.environ['S3_BUCKET'] + '/storage/segmentation/only-panos_data_from_01.06.2020/'
sync_local_s3(local_path, s3_path)

logging.info('All is done')
