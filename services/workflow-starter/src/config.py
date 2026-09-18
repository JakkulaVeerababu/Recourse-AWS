import os

class Settings:
    @property
    def LOG_LEVEL(self) -> str:
        return os.environ.get("LOG_LEVEL", "INFO")

    @property
    def STATE_MACHINE_ARN(self) -> str:
        return os.environ["STATE_MACHINE_ARN"]

settings = Settings()
