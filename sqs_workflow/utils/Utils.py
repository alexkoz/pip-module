import logging
import urllib
import os

class Utils:

    def __init__(self):
        pass

    @staticmethod
    def create_result_s3_key(path_to_s3: str, inference_type: str, inference_id: str, image_id: str,
                             filename: str) -> str:
        s3_path = os.path.join(path_to_s3, inference_type, inference_id, image_id, filename)
        logging.info(f'Created s3 path')
        return s3_path

    @staticmethod
    def download_from_http(url) -> str:
        logging.info(f'Document url:{url} will be downloaded')
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)
        with urllib.request.urlopen(url) as f:
            document = f.read().decode('utf-8')
        return document
