import boto3
import os
from sqs_workflow.tests.QueueMock import QueueMock

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])

# queue = QueueMock()


class SqsProcessor:
    sqs_client = boto3.resource('sqs')

    queue = sqs_client.Queue(os.environ['QUEUE_LINK'])
    queue_str = os.environ['QUEUE_LINK']


    def __init__(self):
        pass

    def send_message(self, message_body):
        req_send = self.queue.send_message(QueueUrl=self.queue_str, MessageBody=message_body)
        print(req_send)
        print(message_body)

    def receive_messages(self, max_number_of_messages: int):
        req_receive = self.queue.receive_messages(QueueUrl=self.queue_str, MaxNumberOfMessages=max_number_of_messages)
        print(req_receive)
        return self

    def delete_message(self, receipt_handle: str):
        self.queue.delete_message(QueueUrl=self.queue_str, ReceiptHandle=receipt_handle)
        return self
