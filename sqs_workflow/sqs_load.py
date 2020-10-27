import sys
import boto3
import os

boto3.setup_default_session(profile_name=os.environ['AWS_PROFILE'],
                            region_name=os.environ['REGION_NAME'])

if __name__ == '__main__':
    sqs_client = boto3.resource('sqs')
    queue = sqs_client.Queue(os.environ['QUEUE_LINK'])

    message_body = "message_body_"
    for i in range(8):
        queue.send_message(MessageBody=message_body + str(i))


sys.exit(0)