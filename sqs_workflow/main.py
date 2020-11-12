from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
import os
import sys
from datetime import datetime
from sqs_workflow.aws.s3.S3Helper import S3Helper
import logging

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

processor = SqsProcessor()
aws_profile = os.environ['AWS_PROFILE']
queue_url = os.environ['QUEUE_LINK']
region_name = os.environ['REGION_NAME']

if __name__ == '__main__':
    logging.info(f"Start the application")
    list_of_messages = processor.pull_messages(1)
    logging.info('Pulled message')
    while len(list_of_messages) > 0:
        for message in list_of_messages:
            message_type = processor.get_attr_value(message, 'messageType')
            processor.process_message_in_subprocess(message_type, message.body)
            processor.complete_processing_message(message)
        logging.info(f"Start pulling messages")
        list_of_messages = processor.pull_messages(1)
logging.info(f"The queue is empty. Exit waiting for next iteration.")
sys.exit(0)
