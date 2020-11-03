from sqs_workflow.SqsProcessor import SqsProcessor
import os
import subprocess
import sys
import json
from datetime import datetime
from sqs_workflow.aws.s3.S3Helper import S3Helper

processor = SqsProcessor()
aws_profile = os.environ['AWS_PROFILE']
queue_url = os.environ['QUEUE_LINK']
region_name = os.environ['REGION_NAME']

if __name__ == '__main__':
    list_of_messages = processor.pull_messages(1)
    for message in list_of_messages:
        message_type = json.loads(message.body)['messageType']
        inference_id = json.loads(message.body)['inferenceId']
        now = datetime.now()
        dt_string = now.strftime("%H-%M-%S")
        s3_path = processor.create_result_s3_key('api/inference/', message_type, inference_id,
                                                 f'result-{dt_string}.json')

        s3_helper = S3Helper()
        s3_helper.save_object_on_s3(s3_path, 'some-content-inside')

        attr_value = processor.get_attr_value(message, "messageType")
        if attr_value == 'similarity':
            result = subprocess.run([sys.executable,  # path to python
                                     os.environ['PATH_TO_SCRIPT'],  # path to script
                                     message.body], universal_newlines=True)
            if not result.returncode == 0:
                print('start panic')
                assert False
sys.exit()
