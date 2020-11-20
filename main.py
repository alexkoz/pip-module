import logging
import os
import sys
from logging.config import fileConfig

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.Utils import Utils

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
    logging.info(f'Pulled messages {len(list_of_messages)} s')
    while len(list_of_messages) > 0:
        for message in list_of_messages:
            message_body = processor.prepare_for_processing(message.body)
            if processor.process_message_in_subprocess(message_body) is not None:
                processor.complete_processing_message(message)
        logging.info(f"Start pulling messages")
        list_of_messages = processor.pull_messages(1)
logging.info(f"The queue is empty. Exit waiting for next iteration.")
sys.exit(0)
