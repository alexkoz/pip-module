import os
import sys
import json
import boto3
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
import logging
import random

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


original_json = "storage/segmentation/pretty-floors_data_from_01.06.2020/order_1017707_floor_1.json"
s3_bucket = "immoviewer-ai-research"

# original_json = 's3://immoviewer-ai-test/storage/segmentation/test-json-w-inference/order_1012550_floor_1.json'

processor = SqsProcessor()
session = boto3.Session(
    aws_access_key_id=os.environ['ACCESS'],
    aws_secret_access_key=os.environ['SECRET']
)
s3 = session.resource('s3')
obj = s3.Object(s3_bucket, original_json)

# todo remove result file from similarity
# todo remove result files from substeps

floor_string = obj.get()['Body'].read().decode('utf-8')
floor_object = json.loads(floor_string)

# todo send major message first
sqs_client = boto3.resource('sqs')
queue = sqs_client.Queue(os.environ['QUEUE_LINK'])
for pano in floor_object['panos']:
    print("List panos to send to separate messages")
    for step in ['ROOMBOX', 'DOOR_DETECTION']:
        del pano['layout']
        message_type = step  # check it
        message = pano
        message['inferenceId'] = random.randint(1, 100)

        req_send = queue.send_message(QueueUrl=os.environ['QUEUE_LINK'], MessageBody=json.dumps(message))


# todo read json
# todo get all panos out of
# todo send individual messages according to steps
# todo send main similarity message

# todo wait till processed
print("All Done")
sys.exit(0)
