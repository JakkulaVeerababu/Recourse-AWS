import os
import boto3

class Settings:
    TABLE_NAME = os.environ.get('TABLE_NAME', 'recourse-development-incidents')
    KMS_KEY_ID = os.environ.get('KMS_KEY_ID')
    DEFAULT_EXPIRATION_MINUTES = int(os.environ.get('DEFAULT_EXPIRATION_MINUTES', '30'))

settings = Settings()
dynamodb = boto3.client('dynamodb')
kms = boto3.client('kms')
