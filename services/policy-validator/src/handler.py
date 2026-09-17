import json
import logging
from .config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle(event, context):
    logger.info(f'Received event in {settings.SERVICE_NAME}', extra={'event': event})
    return {
        'service': settings.SERVICE_NAME,
        'status': 'ready'
    }
