from sqs_workflow.SqsProcessor import SqsProcessor
import os
import sys
from datetime import datetime
from sqs_workflow.aws.s3.S3Helper import S3Helper

processor = SqsProcessor()
aws_profile = os.environ['AWS_PROFILE']
queue_url = os.environ['QUEUE_LINK']
region_name = os.environ['REGION_NAME']

if __name__ == '__main__':
    list_of_messages = processor.pull_messages(1)
    for message in list_of_messages:
        message_type = processor.get_attr_value(message, 'messageType')
        inference_id = processor.get_attr_value(message, 'inferenceId')

        now = datetime.now()
        dt_string = now.strftime("%H-%M-%S")
        s3_path = processor.create_result_s3_key('api/inference/', message_type, inference_id,
                                                 f'result-{dt_string}.json')
        s3_helper = S3Helper()
        s3_helper.save_object_on_s3(s3_path, 'some-content-inside')

        print(f'message_type: {message_type}, inference_id: {inference_id}')

        processor.runs_of_process(message_type, message.body)
        processor.delete_message(message)
sys.exit()
