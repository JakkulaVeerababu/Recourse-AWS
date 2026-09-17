import os

class Settings:
    SERVICE_NAME = 'remediation-executor'
    ENVIRONMENT = os.getenv('RECOURSE_ENVIRONMENT', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

settings = Settings()
