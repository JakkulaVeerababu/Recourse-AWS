import base64
from .config import kms, settings

def encrypt_task_token(token: str) -> str:
    response = kms.encrypt(
        KeyId=settings.KMS_KEY_ID,
        Plaintext=token.encode('utf-8')
    )
    return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
