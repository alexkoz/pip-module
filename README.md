# sqs_workflow module

Environment variables:

```S3_BUCKET```  – Name of your S3 bucket. S3://your-bucket-name/

```ACCESS``` – AWS access key

```SECRET``` – AWS secret key

```REGION_NAME``` – AWS region name

```AWS_PROFILE``` – AWS profile

```QUEUE_LINK``` – SQS Queue URL

```SIMILARITY_SCRIPT``` – Path to 1st dummy script. aids/dummy_similatiry.py

```SIMILARITY_EXECUTABLE``` – Path to executing module for 1st dummy script

```ROOMBOX_SCRIPT``` – Path to 2nd dummy script. aids/dummy_roombox.py

```ROOMBOX_EXECUTABLE```  – Path to executing module for 2nd dummy script

```RMATRIX_SCRIPT``` – Path to 3rd dummy script. aids/dummy_rmatrix.py

```RMATRIX_EXECUTABLE``` – Path to executing module for 3rd dummy script

```SLACK_URL``` – Your Slack App Incoming Webhook URL

```SLACK_ID``` – Slack personal ID if you want to use a mention

If you want connect email notifications:

```GMAIL_USER``` – Your Gmail login. your-login@example.com (Allow insecure app to access your account)

```GMAIL_PASSW``` – Password from your Gmail account

```GMAIL_TO``` – Receiver email address