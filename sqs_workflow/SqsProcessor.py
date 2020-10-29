import boto3
import os

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])


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
        return req_send

    def receive_messages(self, max_number_of_messages: int):
        response_messages = self.queue.receive_messages(QueueUrl=self.queue_str,
                                                        MaxNumberOfMessages=max_number_of_messages)
        return response_messages

    def delete_message(self, message):
        message.delete()

    def purge_queue(self):
        sqs_client = boto3.client('sqs')
        req_purge = sqs_client.purge_queue(QueueUrl=self.queue_str)
        return req_purge
