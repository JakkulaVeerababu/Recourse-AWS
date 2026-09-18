import os

class Settings:
    SERVICE_NAME = "policy-validator"
    INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME", "recourse-development-incidents")
    POLICY_STORE_ID = os.environ.get("POLICY_STORE_ID", "")
    POLICY_VERSION = "recourse-cedar-v1"

settings = Settings()
