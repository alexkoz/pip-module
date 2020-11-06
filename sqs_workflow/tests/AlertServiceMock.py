class AlertServiceMock:
    def __init__(self):
        self.message = None
        self.message_type = None

    def send_slack_message(self, message, message_type):
        self.message = message
        self.message_type = message_type
