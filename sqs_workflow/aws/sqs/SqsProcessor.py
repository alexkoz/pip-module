import hashlib
import json
import logging
import os
import subprocess
import time
from datetime import datetime

import boto3

from sqs_workflow.AlertService import AlertService
from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.Utils import Utils
from sqs_workflow.utils.similarity.SimilarityProcessor import SimilarityProcessor

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])


class SqsProcessor:
    alert_service = AlertService()
    s3_helper = S3Helper()

    sqs_client = boto3.client('sqs')
    sqs_resource = boto3.resource('sqs')

    queue = sqs_resource.Queue(os.environ['QUEUE_LINK'])
    queue_url = os.environ['QUEUE_LINK']
    return_queue_url = os.environ['QUEUE_LINK'] + "-return-queue"

    def __init__(self):
        self.similarity_executable = os.environ['SIMILARITY_EXECUTABLE']
        self.similarity_script = os.environ['SIMILARITY_SCRIPT']
        self.roombox_executable = os.environ['ROOM_BOX_EXECUTABLE']
        self.roombox_script = os.environ['ROOM_BOX_SCRIPT']
        self.rmatrix_executable = os.environ['R_MATRIX_EXECUTABLE']
        self.rmatrix_script = os.environ['R_MATRIX_SCRIPT']

    def get_attr_value(self, message, attribute_name):
        attr_value = json.loads(message.body)[attribute_name]
        return attr_value

    def send_message(self, message_body, queue_url):
        response_send = self.sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)
        logging.info(f'Sent message:{message_body} to queue:{queue_url}')
        return response_send

    def receive_messages(self, max_number_of_messages: int):
        response_messages = self.queue.receive_messages(QueueUrl=self.queue_url,
                                                        MaxNumberOfMessages=max_number_of_messages)
        if len(response_messages) != 0:
            logging.info(f'response_message content:{response_messages[0].body}')

        return response_messages

    def pull_messages(self, number_of_messages: int) -> list:
        attempts = 0
        list_of_messages = self.receive_messages(number_of_messages)
        while attempts < 7 and len(list_of_messages) < number_of_messages:
            messages_received = self.receive_messages(1)
            if len(messages_received) > 0:
                list_of_messages += messages_received
                logging.info(f'Len list of messages:{len(list_of_messages)}')
            else:
                attempts += 1
                time.sleep(2)
            logging.info(f'attempts:{attempts} left')
        if attempts == 7:
            logging.info(f'Out of attempts')
        return list_of_messages

    # todo finish test
    def complete_processing_message(self, message):
        self.send_message(message, self.return_queue_url)  # message.body
        message.delete()
        logging.info(f'Message: {message} is deleted')

    def create_path_and_save_on_s3(self, message_type: str, inference_id: str, processing_result, image_id='asset'):
        s3_path = Utils.create_result_s3_key(StringConstants.COMMON_PREFIX,
                                             message_type,
                                             inference_id,
                                             image_id,
                                             StringConstants.RESULT_FILE_NAME)

        self.s3_helper.save_object_on_s3(s3_path, processing_result)
        logging.info(f'Created S3 object key:{s3_path} content:{processing_result}')

    def process_message_in_subprocess(self, message_type, message_body) -> str:
        processing_result = None
        logging.info('Message type of message: ', message_type)
        message_object = json.loads(message_body)
        inference_id = message_object['inferenceId']
        assert inference_id
        if message_type == ProcessingTypesEnum.Similarity.value:
            logging.info(f'Start processing similarity inference:{inference_id}')
            document_object = SimilarityProcessor.is_similarity_ready(
                self.s3_helper,
                message_object)
            if document_object is not None:
                processing_result = self.run_process(self.similarity_executable,
                                                     self.similarity_script,
                                                     json.dumps(document_object))
                self.create_path_and_save_on_s3(message_type, inference_id, processing_result)
                return processing_result
            else:
                logging.info(f'Document is under processing inference:{inference_id}')
                return None

        image_id = os.path.basename(message_object[StringConstants.PANO_URL_KEY])

        if StringConstants.PRY_MATRIX_KEY not in message_object or message_type == ProcessingTypesEnum.RMatrix.value:
            url_hash = hashlib.md5(message_object[StringConstants.PANO_URL_KEY].encode('utf-8')).hexdigest()
            processing_result = self.check_pry_on_s3(message_type,
                                                     url_hash,
                                                     image_id)
            if processing_result is None:
                logging.info('Processing result is None')
                processing_result = self.run_process(self.rmatrix_executable,
                                                     self.rmatrix_script,
                                                     message_body)
                self.create_path_and_save_on_s3(message_type,
                                                url_hash,
                                                processing_result,
                                                image_id)

        message_object[StringConstants.PRY_MATRIX_KEY] = processing_result

        if message_type == ProcessingTypesEnum.RoomBox.value:
            processing_result = self.run_process(self.roombox_executable,
                                                 self.roombox_script,
                                                 json.dumps(message_object))

        logging.info(f"Finished processing and save result on s3.")
        self.create_path_and_save_on_s3(message_type,
                                        inference_id,
                                        processing_result,
                                        image_id)
        return processing_result

    def run_process(self, executable, script, message_body) -> str:
        subprocess_result = subprocess.run([executable,
                                            script,
                                            message_body],
                                           universal_newlines=True,
                                           capture_output=True)
        if not subprocess_result.returncode == 0:
            at_moment_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            message = f'{at_moment_time}\n SQS processing has failed for process:{executable} script:{script} message:{message_body}.'
            self.alert_service.send_slack_message(message, 0)
        logging.info(f'subprocess code:{subprocess_result.returncode} output:{subprocess_result.stdout}')
        return subprocess_result.stdout

    def check_pry_on_s3(self, message_type: str, url_hash: str, image_id: str) -> str:

        result_s3_key = Utils.create_result_s3_key(StringConstants.COMMON_PREFIX,
                                                   message_type,
                                                   url_hash,
                                                   image_id,
                                                   StringConstants.RESULT_FILE_NAME)

        result = self.s3_helper.is_object_exist(result_s3_key)
        if result is True:
            s3 = boto3.resource('s3')
            path_to_file = os.path.join(result_s3_key, StringConstants.RESULT_FILE_NAME)
            result_object = s3.Object(self.s3_helper.s3_bucket, path_to_file)
            body = result_object.get()['Body'].read().decode('utf-8')
            logging.info(f'result.json in {result_s3_key} exists')
            return body
        else:
            logging.info(f'result.json in {result_s3_key} does not exist')
            return None  # return None when -> str ?
