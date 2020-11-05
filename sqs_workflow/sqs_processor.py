import sys
import os

sys.path.append(os.path.abspath('../'))
from sqs_workflow.aws.sqs.SqsProcessor import SqsProcessor


def dummy_function(message):
    return message


if __name__ == '__main__':
    print("Start processing SQS")
    sqs_processor = SqsProcessor(dummy_function)
    sqs_processor.start_processing_job()

print("All Done with sqs!")
sys.exit(0)
