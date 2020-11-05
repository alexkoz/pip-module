import boto3
import os
import time
import json
import subprocess
import sys
from datetime import datetime
from sqs_workflow.AlertService import AlertService
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])


class SqsProcessor:
    alert_service = AlertService()

    sqs_client = boto3.resource('sqs')

    queue = sqs_client.Queue(os.environ['QUEUE_LINK'])
    queue_str = os.environ['QUEUE_LINK']

    def __init__(self):
        pass

    def get_attr_value(self, message, attribute_name):
        attr_value = json.loads(message.body)[attribute_name]
        return attr_value

    def send_message(self, message_body):
        req_send = self.queue.send_message(QueueUrl=self.queue_str, MessageBody=message_body)
        logging.info(req_send)
        logging.info(f'Message body: {message_body}')
        return req_send

    def receive_messages(self, max_number_of_messages: int):
        response_messages = self.queue.receive_messages(QueueUrl=self.queue_str,
                                                        MaxNumberOfMessages=max_number_of_messages)
        if len(response_messages) != 0:
            logging.info(f'response_message: {response_messages[0].body}')

        return response_messages

    def pull_messages(self, number_of_messages: int) -> list:
        attemps = 0
        list_of_messages = self.receive_messages(number_of_messages)
        while attemps < 7 and len(list_of_messages) < number_of_messages:
            messages_received = self.receive_messages(1)
            if len(messages_received) > 0:
                list_of_messages += messages_received
                logging.info(f'Len list of messages =: {len(list_of_messages)}')

            else:
                attemps += 1
                time.sleep(2)
            logging.info(f'attemps = {attemps}')
        if attemps == 7:
            logging.info(f'Out of attemps')
        return list_of_messages

    def delete_message(self, message):
        message.delete()
        logging.info(f'Message: {message} is deleted')

    def purge_queue(self):
        sqs_client = boto3.client('sqs')
        req_purge = sqs_client.purge_queue(QueueUrl=self.queue_str)
        logging.info(f'Queue is purged')

        return req_purge

    def process_message_in_subprocess(self, message_type, message_body):
        python_execut = sys.executable
        similarity_script = os.environ['PATH_TO_DOOMY_SIMILAR']
        roombox_script = os.environ['PATH_TO_DOOMY_ROOMBOX']
        rmatrix_script = os.environ['PATH_TO_DOOMY_FAILED']

        if message_type == 'similarity':
            self.run_process(python_execut, similarity_script, message_body)

        elif message_type == 'roombox':
            self.run_process(python_execut, roombox_script, message_body)

        elif message_type == 'R_MATRIX':
            self.run_process(python_execut, rmatrix_script, message_body)

    def run_process(self, python_execut, script, message_body):
        result = subprocess.run([python_execut,  # path to python
                                 script,  # path to script
                                 message_body], universal_newlines=True)
        if not result.returncode == 0:
            at_moment_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            message = f'{at_moment_time}\nWarning message in subprocess.'
            self.alert_service.send_slack_message(message, 0)
            # self.alert_service = MockAlert()
            return False

    @staticmethod
    def create_result_s3_key(path_to_s3: str, inference_type: str, inference_id: str, filename: str) -> str:
        s3_path = os.path.join(path_to_s3, inference_type, inference_id, filename)
        logging.info(f'Created s3 path')
        return s3_path
