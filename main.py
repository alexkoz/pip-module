import logging
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from logging.config import fileConfig
from time import sleep

from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor
from sqs_workflow.utils.Utils import Utils

fileConfig(os.path.dirname(os.path.realpath(__file__)) + '/logging_config.ini')
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

if __name__ == '__main__':
    logging.info(f"Start the application")
    executor = ThreadPoolExecutor(2)
    docu_process = executor.submit(SqsProcessor.run_queue_processor, "-docusketch-ai")
    immo_process = executor.submit(SqsProcessor.run_queue_processor, "-immoviewer-ai")
    while not docu_process.done() and not immo_process.done():
        sleep(10)
        logging.info("Keep waiting till all done")

logging.info(f"Both queues are empty. Exit waiting for next iteration.")
sys.exit(0)
