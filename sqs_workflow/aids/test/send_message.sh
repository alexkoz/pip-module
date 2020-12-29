#!/usr/bin/env bash

line_index=1
for entry in `aws s3 --profile clipnow ls s3://immoviewer-ai-research/storage/segmentation/floors_data_from_01.06.2020/`


do
    if [[ $entry == *"json"* ]]; then
        echo "$entry"
        message_id=$(date +%s )
        echo $message_id
        message_body="{ \"inferenceId\":\"zahar-test/$message_id\",  \"messageType\":\"SIMILARITY\",\"orderId\":\"5da5d5164cedfd0050363a2e\",\"documentPath\":\"https://immoviewer-ai-research.s3-eu-west-1.amazonaws.com/storage/segmentation/floors_data_from_01.06.2020/$entry\"}"
          echo "$(date) Message:$line_index message_body:$message_body"
          aws --profile clipnow sqs send-message \
             --region eu-central-1 \
             --queue-url https://eu-central-1.queue.amazonaws.com/700659137911/sandy-immoviewer-ai \
            --message-body "$message_body"
          ((line_index=line_index+1))
          sleep 3s
          echo "$(date) Sent message:$line_index"
    fi

done