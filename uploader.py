import json
import boto3
import os

from datetime import datetime

class Uploader:

    def __init__(self)
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)

                self.serial_no = config['serial_no']
                self.bucket_name = config['bucket_name']

        except:
            print("config.json SN and bucket name fields must be present")

        self.s3_client = boto3.client('s3')
