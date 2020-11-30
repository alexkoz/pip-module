import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from logging.config import fileConfig
from time import sleep

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.Utils import Utils

fileConfig(os.path.dirname(os.path.realpath(__file__)) + '/logging_config.ini')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)


def run_queue_processor(queue_name):
    try:
        logging.info(f'Started process for queue:{queue_name}')
        Utils.check_environment()
        processor = SqsProcessor(queue_name)
        list_of_messages = processor.pull_messages(1)
        logging.info(f'Pulled messages {len(list_of_messages)} s from queue:{queue_name}')
        while len(list_of_messages) > 0:
            for message in list_of_messages:
                #todo swallow the exception
                #todo send slack message if subprocess fails
                #todo send error to return message
                message_body = processor.prepare_for_processing(message.body)
                message_body = processor.process_message_in_subprocess(message_body)
                if message_body is not None:
                    logging.info(f"Setting message body:{message_body}")
                    processor.complete_processing_message(message, message_body)
            logging.info(f"Keep pulling messages queue:{queue_name}")
            list_of_messages = processor.pull_messages(1)
    except Exception as e:
        logging.critical(e, exc_info=True)  # log exception info at CRITICAL log level


if __name__ == '__main__':
    logging.info(f"Start the application")
    executor = ThreadPoolExecutor(2)
    ducu_process = executor.submit(run_queue_processor, "-docusketch-ai")
    immo_process = executor.submit(run_queue_processor, "-immoviewer-ai")
    while not ducu_process.done() and not immo_process.done():
        sleep(10)
        logging.info("Keep waiting till all done")

logging.info(f"Both queues are empty. Exit waiting for next iteration.")
sys.exit(0)
