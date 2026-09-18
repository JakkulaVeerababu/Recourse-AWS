import os

class Settings:
    SERVICE_NAME = 'investigation-agent'
    ENVIRONMENT = os.getenv('RECOURSE_ENVIRONMENT', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    INCIDENT_TABLE_NAME = os.getenv('INCIDENT_TABLE_NAME', 'mock-table')
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'mistral.mistral-large-2402-v1:0')
    BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'ap-south-1')
    PROMPT_VERSION = os.getenv('PROMPT_VERSION', 'recourse-investigator-v1')

settings = Settings()
