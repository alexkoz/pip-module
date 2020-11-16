# sqs_workflow module

Before run an application do:
```bash
bash aids/environment.sh
```

Environment variables:

```S3_BUCKET```  – Name of your S3 bucket. S3://your-bucket-name/

```ACCESS``` – AWS access key

```SECRET``` – AWS secret key

```REGION_NAME``` – AWS region name

```AWS_PROFILE``` – AWS profile

```QUEUE_LINK``` – SQS Queue URL

```SIMILARITY_SCRIPT``` – Path to 1st dummy script. aids/dummy_similarity.py

```SIMILARITY_EXECUTABLE``` – Path to executing module for 1st dummy script

```ROOM_BOX_SCRIPT``` – Path to 2nd dummy script. aids/dummy_roombox.py

```ROOM_BOX_EXECUTABLE```  – Path to executing module for 2nd dummy script

```R_MATRIX_SCRIPT``` – Path to 3rd dummy script. aids/dummy_rmatrix.py

```R_MATRIX_EXECUTABLE``` – Path to executing module for 3rd dummy script

```DOOR_DETECTION_SCRIPT``` – Path to 4th dummy script. aids/dummy_dd.py

```DOOR_DETECTION_EXECUTABLE``` – Path to executing module for 4th dummy script

```INPUT_DIRECTORY``` – Path to input directory for the prepare-for-processing method

```OUTPUT_DIRECTORY``` – Path to output directory for the prepare-for-processing method

```SLACK_URL``` – Your Slack App Incoming Webhook URL

```SLACK_ID``` – Slack personal ID if you want to use a mention

If you want connect email notifications:

```GMAIL_USER``` – Your Gmail login. your-login@example.com (Allow insecure app to access your account)

```GMAIL_PASSW``` – Password from your Gmail account

```GMAIL_TO``` – Receiver email address