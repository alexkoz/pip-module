import boto3
import os
import time
import json
import subprocess
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
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
        self.similarity_executable = os.environ['SIMILARITY_EXECUTABLE']
        self.similarity_script = os.environ['SIMILARITY_SCRIPT']
        self.roombox_executable = os.environ['ROOMBOX_EXECUTABLE']
        self.roombox_script = os.environ['ROOMBOX_SCRIPT']
        self.rmatrix_executable = os.environ['RMATRIX_EXECUTABLE']
        self.rmatrix_script = os.environ['RMATRIX_SCRIPT']

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

    def process_message_in_subprocess(self, message_type, message_body) -> str:
        processing_result = None
        # todo add explicit logging
        if message_type == ProcessingTypesEnum.Similarity:
            processing_result = self.run_process(self.similarity_executable,
                                                 self.similarity_script,
                                                 message_body)

        elif message_type == ProcessingTypesEnum.RoomBox:
            processing_result = self.run_process(self.roombox_executable,
                                                 self.roombox_script,
                                                 message_body)

        elif message_type == ProcessingTypesEnum.RMatrix:
            processing_result = self.run_process(self.rmatrix_executable,
                                                 self.rmatrix_script,
                                                 message_body)
        return processing_result

    def run_process(self, executable, script, message_body) -> str:

        # todo add explicit logging
        subprocess_result = subprocess.run([executable,
                                            script,
                                            message_body], universal_newlines=True)
        if not subprocess_result.returncode == 0:
            at_moment_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            message = f'{at_moment_time}\n SQS processing has failed for process:{executable} script:{script} message:{message_body}.'
            self.alert_service.send_slack_message(message, 0)
        return subprocess_result

    @staticmethod
    def create_result_s3_key(path_to_s3: str, inference_type: str, inference_id: str, filename: str) -> str:
        s3_path = os.path.join(path_to_s3, inference_type, inference_id, filename)
        logging.info(f'Created s3 path')
        return s3_path
