import os
import requests
import json
import smtplib
from email.mime.text import MIMEText
import logging


class AlertService:
    def __init__(self):
        pass

    @staticmethod
    def send_slack_message(message, msg_type):
        """
        types: 0 - without mention,
        1 - with mention somebody
        """
        try:
            slack_url = os.environ['SLACK_URL']
            slack_id = os.environ['SLACK_ID']

            if msg_type == 0:
                message_text = message
                data = {'text': message_text}
                requests.post(url=slack_url, data=json.dumps(data))
                logging.info('Sent common message in Slack')

            elif msg_type == 1:
                message_text = message + ' <@' + slack_id + '>'
                data = {'text': message_text}
                requests.post(url=slack_url, data=json.dumps(data))
                logging.info('Sent message w/ mention in Slack')
        except:
            logging.info('No environment variable for Slack. Check SLACK_URL, SLACK_ID')

    @staticmethod
    def send_email_message(message):
        try:
            gmail_user = os.environ['GMAIL_USER']
            gmail_password = os.environ['GMAIL_PASSW']
            gmail_to = os.environ['GMAIL_TO']

            fromx = gmail_user
            to = gmail_to
            msg = MIMEText(message)
            msg['Subject'] = 'AWS Cost Report Message'
            msg['From'] = fromx
            msg['To'] = to
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(gmail_user, gmail_password)
                server.sendmail(fromx, to, msg.as_string())
                server.quit()
                logging.info('Email sent')
            except:
                logging.info('Something wrong :(')
        except:
            logging.info('No environment variable for GMail. Check GMAIL_USER, GMAIL_PASSW, GMAIL_TO')
            pass
