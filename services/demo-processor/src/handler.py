import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle(event, context):
    request_id = context.aws_request_id if hasattr(context, 'aws_request_id') else 'local-request'
    
    # Process a lightweight deterministic operation
    metadata = {
        'awsRequestId': request_id,
        'timestamp': datetime.utcnow().isoformat(),
        'demoMode': event.get('demoMode', 'NORMAL'),
        'invocationSource': event.get('source', 'unknown'),
        'service': 'demo-processor',
    }
    
    logger.info(f"Processed request", extra={'event': metadata})
    
    return {
        'service': 'demo-processor',
        'status': 'processed',
        'requestId': request_id
    }
