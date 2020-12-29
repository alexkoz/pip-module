import json
import os


class MessageMock:
    def __init__(self):
        self.body = ''


class RunProcessMock:

    def __init__(self):
        self.message_body = None
        self.list_of_messages = None
        self.messages_queue = None
        pass

    def pull_messages_mock(self, number_of_messages) -> list:
        if self.list_of_messages is not None:
            return []

        self.list_of_messages = []

        input_processing_directory = os.environ['INPUT_DIRECTORY']
        output_processing_directory = os.environ['OUTPUT_DIRECTORY']

        input_path = os.path.join(input_processing_directory,
                                  'fccc6d02b113260b57db5569e8f9c897', 'order_1012550_floor_1.json.json')
        output_path = os.path.join(output_processing_directory, 'fccc6d02b113260b57db5569e8f9c897')

        roombox_message = MessageMock()
        roombox_message.body = json.dumps(
            {"messageType": "SIMILARITY", "orderId": "5d36c94fc9e77c0054fbab02", "floor": 0,
             "documentPath": "https://immoviewer-ai-research.s3-eu-west-1.amazonaws.com/storage/segmentation/floors_data_from_01.06.2020_with_address/order_1013678_floor_1.json"})
        # roombox_message = json.dumps(roombox_message)
        self.list_of_messages.append(roombox_message)
        return self.list_of_messages

    def complete_processing_message_mock(self, message, message_body: str):
        # return f'sent_message_body_to_return_queue'
        self.messages_queue = [message_body]
        return self.messages_queue

    def prepare_for_processing_mock(self, message_body):
        return json.dumps(message_body)

    def process_message_in_subprocess_mock(self, message_body):
        self.message_body = json.loads(message_body)
        return message_body

    def process_message_in_subprocess_none_mock(self, message_body):
        return None
