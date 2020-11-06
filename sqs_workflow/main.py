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
    list_of_messages = processor.pull_messages(1)
    logging.info('Pulled message')
    for message in list_of_messages:
        message_type = processor.get_attr_value(message, 'messageType')

        inference_id = processor.get_attr_value(message, 'inferenceId')
        logging.info(f'Message type: {message_type} Inference ID: {inference_id}')

        #todo if message relies on previous messages check

        processing_result = processor.process_message_in_subprocess(message_type, message.body)

        dt_string = datetime.now().strftime("%H-%M-%S")
        s3_path = processor.create_result_s3_key('api/inference/',
                                                 message_type,
                                                 inference_id,
                                                 'result.json')
        s3_helper = S3Helper()
        s3_helper.save_object_on_s3(s3_path, processing_result)

        processor.delete_message(message)
sys.exit()
