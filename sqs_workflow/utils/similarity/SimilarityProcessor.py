import json
import logging

import numpy as np

from sqs_workflow.aws.s3.S3Helper import S3Helper
from sqs_workflow.utils.StringConstants import StringConstants


class SimilarityProcessor:

    @staticmethod
    def is_similarity_ready(s3_helper: S3Helper, message_object) -> bool:
        # todo if similarity document is existing for further processing
        similarity_document = message_object['similarity_document']
        if s3_helper.is_object_exist(similarity_document):
            logging.info(f'Found similarity document:{similarity_document} return True')
            return True
        logging.info(f'There is no similarity document:{similarity_document}')
        # todo get message steps if any
        list_results_keys = []
        final_document = {}
        for panorama in message_object['panos']:

            logging.info(f'Start processing step:{panorama} for document:{similarity_document}')
            # todo list all images first
            for step in message_object['steps']:
                logging.info(f'Start processing panorama:{panorama} for step:{step}')
                s3_result_key = ""
                if not s3_helper.is_object_exist(s3_result_key):
                    logging.info(f'Could not find result for panorama:{panorama} for step:{step}')
                    logging.info(f'Similarity:{similarity_document} is not ready yet')
                    return False
                else:
                    list_results_keys.append(s3_result_key)
                    logging.info(f'Panorama:{panorama} for step:{step} is processed')

                pass
        logging.info(f'All {len(list_results_keys)} steps for similarity are done.')

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
