import os

class Settings:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    INCIDENT_TABLE_NAME = os.environ.get("INCIDENT_TABLE_NAME")
    MAX_LOGS = int(os.environ.get("MAX_LOGS", "100"))
    MAX_LOG_MESSAGE_LENGTH = int(os.environ.get("MAX_LOG_MESSAGE_LENGTH", "2000"))
    METRICS_WINDOW_BEFORE_MINUTES = int(os.environ.get("METRICS_WINDOW_BEFORE_MINUTES", "10"))
    METRICS_WINDOW_AFTER_MINUTES = int(os.environ.get("METRICS_WINDOW_AFTER_MINUTES", "5"))
    LOGS_WINDOW_BEFORE_MINUTES = int(os.environ.get("LOGS_WINDOW_BEFORE_MINUTES", "5"))
    LOGS_WINDOW_AFTER_MINUTES = int(os.environ.get("LOGS_WINDOW_AFTER_MINUTES", "5"))

settings = Settings()
