from sqs_workflow.SqsProcessor import SqsProcessor
import os
import subprocess
import sys


processor = SqsProcessor()
aws_profile = os.environ['AWS_PROFILE']
queue_url = os.environ['QUEUE_LINK']
region_name = os.environ['REGION_NAME']


if __name__ == '__main__':
    list_of_messages = processor.pull_messages(2)
    for message in list_of_messages:
        attr_value = processor.get_attr_value(message, "messageType")
        if attr_value == 'SIMILARITY':
            result = subprocess.run([sys.executable,  # path to python
                                     os.environ['PATH_TO_SCRIPT'],  # path to script
                                     message.body], universal_newlines=True)
            if not result.returncode == 0:
                print('start panic')
                assert False
sys.exit()
