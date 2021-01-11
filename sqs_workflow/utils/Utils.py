import logging
import urllib
import os
import requests
import shutil
import hashlib


class Utils:

    def __init__(self):
        pass

    @staticmethod
    def check_environment():

        assert os.environ['S3_BUCKET']
        assert os.environ['S3_REGION']

        for profile in ['DOCU', 'IMMO']:
            assert os.environ[f'{profile}_ACCESS']
            assert os.environ[f'{profile}_SECRET']
            assert os.environ[f'{profile}_REGION_NAME']
            assert os.environ[f'{profile}_AWS_PROFILE']

        assert os.environ['APP_BRANCH']
        assert os.environ['SIMILARITY_EXECUTABLE']
        assert os.environ['SIMILARITY_SCRIPT']
        assert os.environ['ROOM_BOX_EXECUTABLE']
        assert os.environ['ROOM_BOX_SCRIPT']
        assert os.environ['R_MATRIX_EXECUTABLE']
        assert os.environ['R_MATRIX_SCRIPT']
        assert os.environ['DOOR_DETECTION_SCRIPT']
        assert os.environ['DOOR_DETECTION_EXECUTABLE']
        assert os.environ['ROTATE_EXECUTABLE']
        assert os.environ['ROTATE_SCRIPT']
        assert os.environ['INPUT_DIRECTORY']
        assert os.environ['OUTPUT_DIRECTORY']
        assert os.environ['SLACK_URL']
        assert os.environ['SLACK_ID']
        assert os.environ['GMAIL_USER']
        assert os.environ['GMAIL_PASSW']
        assert os.environ['GMAIL_TO']

    @staticmethod
    def create_result_s3_key(path_to_s3: str,
                             inference_type: str,
                             inference_id: str,
                             image_id: str,
                             filename: str) -> str:
        s3_path = os.path.join(path_to_s3, inference_type, inference_id, image_id, filename)
        logging.info(f'Created s3 path:{s3_path}')
        return s3_path

    @staticmethod
    def download_from_http(url: str, absolute_file_path=None) -> str:
        if not url.endswith('.json'):
            return Utils.download_from_http_and_save(url, absolute_file_path)
        logging.info(f'Document url:{url} will be downloaded')
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)
        with urllib.request.urlopen(url) as f:
            document = f.read().decode('utf-8')
            if absolute_file_path:
                with open(absolute_file_path, 'w') as document_file:
                    document_file.write(document)
                    document_file.close()
        return document

    @staticmethod
    def download_from_http_and_save(url, absolute_file_path):
        logging.info(f'Document url:{url} will be downloaded')

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(absolute_file_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            logging.info(f'Image sucessfully Downloaded:{absolute_file_path}')
        else:
            logging.info('Image Couldn\'t be retreived')
            raise Exception(f"Image:{url} is not downloaded")

    @staticmethod
    def generate_image_hash(url: str) -> str:
        generated_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return generated_hash
