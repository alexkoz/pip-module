import boto3
import os

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])


class SqsProcessor:
    sqs_client = boto3.resource('sqs')

    queue = sqs_client.Queue(os.environ['APP_BRANCH'])
    queue_str = os.environ['APP_BRANCH']

    def __init__(self):
        pass

    def send_message(self, message_body):
        req = self.queue.send_message(QueueUrl=self.queue_str, MessageBody=message_body)
        print(req)
        print(message_body)

    # def receive_messages(self, max_number_of_messages: int):
    #     req = self.queue.receive_messages(QueueUrl=self.queue_str, MaxNumberOfMessages=max_number_of_messages)
    #     print(req)
    #     return self

    def delete_message(self, receipt_handle: str):
        self.queue.delete_message(QueueUrl=self.queue_str, ReceiptHandle=receipt_handle)
        return self

