import json
import logging
import os

import numpy as np

from sqs_workflow.aws.s3.S3Helper import S3Helper
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
            logging.info(f'There is no similarity document:{steps_document}')
            list_results_keys = []
            for panorama in steps_document[StringConstants.PANOS_KEY]:

                logging.info(f'Start processing step:{panorama}')

                for step in steps_document[StringConstants.STEPS]:
                    logging.info(f'Start processing panorama:{panorama} for step:{step}')
                    s3_result_key = Utils.create_result_s3_key(StringConstants.COMMON_PREFIX,
                                                               step,
                                                               str(message_object[StringConstants.INFERENCE_ID_KEY]),
                                                               os.path.basename(panorama[StringConstants.PANO_URL_KEY]),
                                                               StringConstants.RESULT_FILE_NAME)

                    if not s3_helper.is_object_exist(s3_result_key):
                        logging.info(f'Could not find result for panorama:{panorama} for step:{step}')
                        logging.info(f'Similarity step document for panorma:{panorama} is not ready yet')
                        return None
                    else:
                        list_results_keys.append(s3_result_key)
                        logging.info(f'Panorama:{panorama} for step:{step}, key:{s3_result_key} is processed')

            document_object = SimilarityProcessor.assemble_results_into_document(
                s3_helper,
                message_object,
                list_results_keys)
            logging.info(f'All {len(list_results_keys)} steps for similarity are done.')
        return document_object

    # todo test method
    @staticmethod
    def assemble_results_into_document(s3_helper: S3Helper, message_object, list_results_keys):

        panos = {}
        for s3_key in list_results_keys:
            logging.info(f'Start processing key:{s3_key}')
            step_result = json.loads(s3_helper.read_s3_object(s3_key))
            if step_result[StringConstants.PANO_URL_KEY] in panos:
                panos[step_result[StringConstants.PANO_URL_KEY]] = {**step_result,
                                                                    **panos[step_result[StringConstants.PANO_URL_KEY]]}
                logging.info(f'Key:{s3_key} is in list and merged:{panos[step_result[StringConstants.PANO_URL_KEY]]}')
            else:
                panos[step_result[StringConstants.PANO_URL_KEY]] = step_result
                logging.info(f'Key:{s3_key} is not in list. Result:{step_result}')

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
