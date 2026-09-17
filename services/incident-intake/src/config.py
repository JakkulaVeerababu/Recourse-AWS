import os

class Settings:
    SERVICE_NAME = 'incident-intake'
    ENVIRONMENT = os.getenv('RECOURSE_ENVIRONMENT', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "recourse-development-incidents")
    IDEMPOTENCY_TTL_DAYS = int(os.environ.get("IDEMPOTENCY_TTL_DAYS", "7"))

settings = Settings()
