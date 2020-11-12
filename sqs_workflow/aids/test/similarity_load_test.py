import json
import logging
import os
import random
import sys
from pathlib import Path

import boto3

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.StringConstants import StringConstants


def purge_queue(queue_url):
    sqs_client = boto3.client('sqs')
    req_purge = sqs_client.purge_queue(QueueUrl=queue_url)
    logging.info(f'Queue is purged')
    return req_purge


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

original_json = "storage/segmentation/pretty-floors_data_from_01.06.2020/order_1017707_floor_1.json"
s3_bucket = "immoviewer-ai-test"

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

sqs_client = boto3.resource('sqs', region_name=os.environ['REGION_NAME'])
queue = sqs_client.Queue(os.environ['QUEUE_LINK'])

# todo send major message first
purge_queue(os.environ['QUEUE_LINK'])

similarity_test_message = {
    "messageType": "SIMILARITY",
    "orderId": "5da5d5164cedfd0050363a2e",
    "inferenceId": 1111,
    "floor": 1,
    "tourId": "1342386",
    "documentPath": "urljson",
    "stepsDocumentPath": "https://immoviewer-ai-test.s3-eu-west-1.amazonaws.com/storage/segmentation/only-panos_data_from_01.06.2020/order_1012550_floor_1.json.json",
    "steps": ['ROOMBOX']
}

req_send = queue.send_message(QueueUrl=os.environ['QUEUE_LINK'], MessageBody=json.dumps(similarity_test_message))
#
panos_counter = 0
for pano in floor_object['panos']:
    panos_counter += 1
    print("List panos to send to separate messages")
    del pano['layout']
    for step in [StringConstants.ROOM_BOX_KEY, StringConstants.DOOR_DETECTION_KEY]:
        message = pano
        message['inferenceId'] = random.randint(1, 100)
        req_send = queue.send_message(QueueUrl=os.environ['QUEUE_LINK'], MessageBody=json.dumps(message))

main_script_path = os.path.join(str(Path.home()), 'projects', 'sqs_workflow', 'sqs_workflow') + '/main.py'
for i in range(panos_counter + 1):
    list_of_messages = processor.pull_messages(1)
    logging.info('Pulled message')
    for message in list_of_messages:
        if 'messageType' in json.loads(message.body):
            message_type = json.loads(message.body)['messageType']
            # if message_message_type == 'SIMILARITY':
            #     message_type = 'SIMILARITY'
        else:
            message_type = 'ROOM_BOX'
        processor.process_message_in_subprocess(message_type, message.body)

# todo read json
# todo get all panos out of
# todo send individual messages according to steps
# todo send main similarity message

# todo wait till processed
print("All Done")
sys.exit(0)
