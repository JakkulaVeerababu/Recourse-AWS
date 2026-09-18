import json
import logging
import re
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
from src.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

sfn_client = boto3.client('stepfunctions')

def handle(event: Dict[str, Any], context) -> Dict[str, Any]:
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        detail = event.get('detail', {})
        if not detail:
            return {"status": "ignored", "reason": "No detail in event"}
            
        incident_id = detail.get('incident_id')
        if not incident_id:
            return {"status": "ignored", "reason": "No incident_id in event detail"}
            
        # Sanitize incident_id for Step Functions execution name constraints
        # Step Functions allows: letters, numbers, -, _, . (max 80 chars)
        execution_name = re.sub(r'[^a-zA-Z0-9\-_.]', '_', incident_id)[:80]
        
        try:
            response = sfn_client.start_execution(
                stateMachineArn=settings.STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps(event)
            )
            logger.info(f"Started orchestration execution {response['executionArn']} for incident {incident_id}")
            return {"status": "success", "executionArn": response['executionArn']}
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ExecutionAlreadyExists':
                logger.info(f"Execution {execution_name} already exists for incident {incident_id}. Idempotent success.")
                return {"status": "success", "note": "ExecutionAlreadyExists"}
            raise e
            
    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        return {"status": "error", "reason": str(e)}
