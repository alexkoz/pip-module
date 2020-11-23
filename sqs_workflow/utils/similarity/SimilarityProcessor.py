import json
import logging
import os
from typing import List

import numpy as np

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.ProcessingTypesEnum import ProcessingTypesEnum
from sqs_workflow.utils.StringConstants import StringConstants
from sqs_workflow.utils.Utils import Utils


class SimilarityProcessor:

    @staticmethod
    def is_similarity_ready(s3_helper: S3Helper, message_object):

        if StringConstants.DOCUMENT_PATH_KEY in message_object:
            logging.info(f'Found similarity return True')
            document_object = json.loads(Utils.download_from_http(message_object[StringConstants.DOCUMENT_PATH_KEY]))
        else:
            steps_document = json.loads(
                Utils.download_from_http(message_object[StringConstants.STEPS_DOCUMENT_PATH_KEY]))
            logging.info(f'There is no similarity document: {steps_document}')
            list_results_keys = []
            for panorama in steps_document[StringConstants.PANOS_KEY]:

                logging.info(f'Start processing panorama: {panorama}')

                for step in message_object[StringConstants.STEPS_KEY]:
                    logging.info(f'Start processing panorama: {panorama} for step: {step}')
                    s3_result_key = Utils.create_result_s3_key(StringConstants.COMMON_PREFIX,
                                                               step,
                                                               str(message_object[StringConstants.INFERENCE_ID_KEY]),
                                                               os.path.basename(panorama[StringConstants.PANO_URL_KEY]),
                                                               StringConstants.RESULT_FILE_NAME)

                    if not s3_helper.is_object_exist(s3_result_key):
                        logging.info(f'Could not find result for panorama: {panorama} for step: {step}')
                        logging.info(f'Similarity step document for panorma: {panorama} is not ready yet')
                        return None
                    else:
                        list_results_keys.append(s3_result_key)
                        logging.info(f'Panorama: {panorama} for step: {step}, key: {s3_result_key} is processed')

            document_object = SimilarityProcessor.assemble_results_into_document(
                s3_helper,
                message_object,
                list_results_keys)
            logging.info(f'All {len(list_results_keys)} steps for similarity are done.')
        return document_object

    @staticmethod
    def assemble_results_into_document(s3_helper: S3Helper, message_object, list_results_keys):

        panos = {}
        for s3_key in list_results_keys:
            logging.info(f'Start processing key:{s3_key}')
            step_result = json.loads(s3_helper.read_s3_object(s3_key))
            s3_key_short = '/'.join(s3_key.split('/')[-3:])
            if s3_key_short in panos:
                for pano in message_object[StringConstants.PANOS_KEY]:
                    if os.path.basename(pano[StringConstants.PANO_URL_KEY]) == s3_key.split('/')[-2]:
                        panos[s3_key_short]['layout'].extend(step_result)
                        logging.info(f'Key: {s3_key} is in list and merged: {panos[s3_key_short]}')
            else:
                for pano in message_object[StringConstants.PANOS_KEY]:
                    if os.path.basename(pano[StringConstants.PANO_URL_KEY]) == s3_key.split('/')[-2]:
                        panos[s3_key_short] = pano
                        panos[s3_key_short]['layout'] = step_result
                        logging.info(f'Key: {s3_key_short} is not in list. Result: {step_result}')

        message_object[StringConstants.PANOS_KEY] = list(panos.values())
        logging.info(f'Returning message with {len(message_object[StringConstants.PANOS_KEY])} panos')
        return message_object

    @staticmethod
    def create_layout_object(step, result):
        layout_object = []
        if step == StringConstants.ROOM_BOX_KEY:
            result_object = json.loads(result)
            room_box = np.array(result_object['layout']['uv']).astype(np.float)
            room_box = (room_box - [0.5, 0.5]) * [360, 180]
            print(room_box)
            for point in room_box:
                layout_object.append({
                    "x": point[0],
                    "y": point[1],
                    "type": "corner"
                })

            return layout_object
        if step == StringConstants.DOOR_DETECTION_KEY:
            pass
        return layout_object

    @staticmethod
    def generate_message(pano_info, steps):
        # result_messages = []
        result_message = {}
        for step in steps:
            for key in pano_info.keys():
                result_message[StringConstants.MESSAGE_TYPE_KEY] = step
                result_message[key] = pano_info.get(key)
                # result_messages.append(result_message)
        return result_message

    @staticmethod
    def start_pre_processing(message_object, input_path: str) -> List[str]:
        logging.info(f"Start pre-processing message:{message_object}, input:{input_path}")
        list_messages = []

        document_absolute_path = os.path.join(input_path,
                                              os.path.basename(message_object[StringConstants.DOCUMENT_PATH_KEY]))
        with open(document_absolute_path) as f:
            document = json.load(f)
            f.close()

        for step in message_object[StringConstants.STEPS_KEY]:
            for pano in document[StringConstants.PANOS_KEY]:
                message = message_object.copy()
                del message[StringConstants.DOCUMENT_PATH_KEY]
                message[StringConstants.PANO_URL_KEY] = pano[StringConstants.PANO_URL_KEY]
                message[StringConstants.MESSAGE_TYPE_KEY] = step
                list_messages.append(json.dumps(message))

        similarity_message = message_object.copy()
        if StringConstants.DOCUMENT_PATH_KEY in similarity_message:
            del similarity_message[StringConstants.DOCUMENT_PATH_KEY]
        similarity_message[StringConstants.MESSAGE_TYPE_KEY] = ProcessingTypesEnum.Similarity.value
        list_messages.append(json.dumps(similarity_message))
        logging.info(f"Created list of messages:{list_messages}")
        return list_messages
