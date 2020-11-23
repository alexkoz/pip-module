import logging
import subprocess
from datetime import datetime
from sqs_workflow.AlertService import AlertService


class AlertServiceMock:
    alert_service = AlertService()

    def __init__(self):
        self.message = None
        self.message_type = None

    def send_slack_message(self, message, message_type):
        self.message = message
        self.message_type = message_type

    def run_process(self, executable, script, message_body) -> str:
        logging.info(f"Start process executable:{executable} script:{script} message:{message_body}")
        subprocess_result = subprocess.run([executable,
                                            script,
                                            message_body],
                                           universal_newlines=True,
                                           capture_output=True)
        if not subprocess_result.returncode == 0:
            at_moment_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            message = f'{at_moment_time}\n SQS processing has failed for process:{executable} script:{script} message:{message_body}.'
            self.alert_service.send_slack_message(message, 0)
        logging.info(f'subprocess code: {subprocess_result.returncode} output:{subprocess_result.stdout}')
        return subprocess_result.stdout
