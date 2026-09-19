import logging
from typing import Dict, Any
from .crypto import encrypt_task_token
from .repository import create_approval_request

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info("Received approval request trigger", extra={"event": {k: v for k, v in event.items() if k != 'taskToken'}})
    
    incident_id = event.get('incident_id')
    task_token = event.get('taskToken')
    
    if not incident_id or not task_token:
        logger.error("Missing incident_id or taskToken")
        raise ValueError("Missing incident_id or taskToken")
        
    encrypted_token = encrypt_task_token(task_token)
    approval_id, requested_at = create_approval_request(incident_id, event, encrypted_token)
    
    logger.info(f"Successfully generated approval request {approval_id}")
    
    return {
        "approval_request_id": approval_id,
        "requested_at": requested_at,
        "status": "PENDING"
    }
