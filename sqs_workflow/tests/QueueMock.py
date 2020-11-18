import random
import logging


class QueueMock:

    def __init__(self):
        self.queue_messages = []

    def generate_mock_messages(self):
        message = {'Body': 'text' + str(random.randint(2001, 2999)),
                   'MessageId': random.randint(1, 30)}
        self.queue_messages.append(message)
        return message

    def receive_messages_from_queue(self, max_number_of_messages):
        logging.info('Start receiving messages')
        messages = []
        for i in range(max_number_of_messages):
            message = self.generate_mock_messages()
            messages.append(message)
        return self.queue_messages.copy()

    def send_message_to_queue(self, message_body, queue_url):
        logging.info('Start send message')
        message = {'Body': message_body,
                   'MessageId': random.randint(1, 30)}
        self.queue_messages.append(message)
        return self.queue_messages

    def delete_message(self, message_body_to_delete):
        for message in self.queue_messages:
            if message['Body'] == message_body_to_delete:
                self.queue_messages.remove(message)
        logging.info(f'Received and deleted message: {message_body_to_delete}')
        return self
