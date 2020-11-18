#!/usr/bin/env bash

SQS_PROCESSOR_PID=`ps aux | grep "/home/ubuntu/projects/python/misc/sqs_workflow/main.py" | grep -v grep | awk '{print $2}'`

echo "SQS_PROCESSOR_PID is [${SQS_PROCESSOR_PID}]"

if [[ ${SQS_PROCESSOR_PID} ]]
then
  echo 'sqs_workflow is running'
else
	echo 'sqs_workflow not running has to start'
	cd /home/ubuntu/projects/python/misc/sqs_workflow
	"/home/ubuntu/projects/python/misc/sqs_workflow/venv/bin/python"  "/home/ubuntu/projects/python/misc/sqs_workflow/main.py" >> "/home/ubuntu/groovy/sqs-workflow.log"
fi
