import random
import logging


class QueueMock:

    def __init__(self):
        self.queue_messages = []
        self.return_queue_messages = []

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

    def send_message_to_return_queue(self, message):
        logging.info('Start send message to return queue')
        self.return_queue_messages.append(message)

    def delete_message(self, message_body_to_delete):
        for message in self.queue_messages:
            if message['Body'] == message_body_to_delete:
                self.queue_messages.remove(message)
        logging.info(f'Received and deleted message: {message_body_to_delete}')
        return self

    def complete_processing_message(self, message):
        self.send_message_to_return_queue(message)
        for message_in_queue in self.queue_messages:
            if message_in_queue['Body'] == message:
                self.queue_messages.remove(message_in_queue)
                logging.info(f'Message: {message} is deleted')
            else:
                logging.info(f'Message {message} not in queue')
