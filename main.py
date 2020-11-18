from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
import os
import sys
from sqs_workflow.utils.Utils import Utils
import logging
from logging.config import fileConfig

fileConfig(os.path.dirname(os.path.realpath(__file__)) + '/logging_config.ini')

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


processor = SqsProcessor()
aws_profile = os.environ['AWS_PROFILE']
queue_url = os.environ['QUEUE_LINK']
region_name = os.environ['REGION_NAME']

if __name__ == '__main__':
    logging.info(f"Start the application")
    Utils.check_environment()
    list_of_messages = processor.pull_messages(1)
    logging.info('Pulled message')
    while len(list_of_messages) > 0:
        for message in list_of_messages:
            message_body = processor.prepare_for_processing(message.body)
            processor.process_message_in_subprocess(message_body)
            processor.complete_processing_message(message)
        logging.info(f"Start pulling messages")
        list_of_messages = processor.pull_messages(1)
logging.info(f"The queue is empty. Exit waiting for next iteration.")
sys.exit(0)
