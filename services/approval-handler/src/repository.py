import uuid
from datetime import datetime, timezone
import base64
from typing import Dict, Any, Optional
from .config import dynamodb, kms, sfn, settings

def get_incident_meta(incident_id: str) -> Optional[Dict[str, Any]]:
    response = dynamodb.get_item(
        TableName=settings.TABLE_NAME,
        Key={'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': 'META'}}
    )
    item = response.get('Item')
    if not item: return None
    return {k: list(v.values())[0] for k, v in item.items()}

def get_approval_request(incident_id: str, approval_id: str) -> Optional[Dict[str, Any]]:
    response = dynamodb.get_item(
        TableName=settings.TABLE_NAME,
        Key={'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': f"APPROVAL#{approval_id}"}}
    )
    item = response.get('Item')
    if not item: return None
    return {k: list(v.values())[0] for k, v in item.items()}

def decrypt_task_token(encrypted_token: str) -> str:
    response = kms.decrypt(
        KeyId=settings.KMS_KEY_ID,
        CiphertextBlob=base64.b64decode(encrypted_token)
    )
    return response['Plaintext'].decode('utf-8')

def process_decision(incident_id: str, approval_id: str, decision: str, reason: str, approver_sub: str, approver_username: str) -> bool:
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    new_status = 'APPROVED' if decision == 'APPROVE' else 'REJECTED'
    incident_status = 'AUTHORIZED' if decision == 'APPROVE' else 'REJECTED'
    
    try:
        dynamodb.update_item(
            TableName=settings.TABLE_NAME,
            Key={'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': f"APPROVAL#{approval_id}"}},
            UpdateExpression="SET #status = :newStatus, #decision = :decision, #decidedAt = :now, #sub = :sub, #uname = :uname, #reason = :reason, #updatedAt = :now",
            ConditionExpression="#status = :pending AND attribute_not_exists(#decidedAt)",
            ExpressionAttributeNames={
                '#status': 'status', '#decision': 'decision', '#decidedAt': 'decidedAt',
                '#sub': 'approverSub', '#uname': 'approverUsername', '#reason': 'decisionReason', '#updatedAt': 'updatedAt'
            },
            ExpressionAttributeValues={
                ':pending': {'S': 'PENDING'}, ':newStatus': {'S': new_status}, ':decision': {'S': decision},
                ':now': {'S': now}, ':sub': {'S': approver_sub}, ':uname': {'S': approver_username}, ':reason': {'S': reason or ""}
            }
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        req = get_approval_request(incident_id, approval_id)
        if req and req.get('status') == new_status and req.get('approverSub') == approver_sub:
            return True
        return False

    dynamodb.update_item(
        TableName=settings.TABLE_NAME,
        Key={'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': 'META'}},
        UpdateExpression="SET #status = :incStatus, #investigationStage = :stage, #approvalStatus = :newStatus, #approvalDecidedAt = :now, #updatedAt = :now, #version = #version + :one",
        ExpressionAttributeNames={
            '#status': 'status', '#investigationStage': 'investigationStage', '#approvalStatus': 'approvalStatus',
            '#approvalDecidedAt': 'approvalDecidedAt', '#updatedAt': 'updatedAt', '#version': 'version'
        },
        ExpressionAttributeValues={
            ':incStatus': {'S': incident_status}, ':stage': {'S': 'APPROVAL_COMPLETE'}, ':newStatus': {'S': new_status},
            ':now': {'S': now}, ':one': {'N': '1'}
        }
    )
    
    event_id = str(uuid.uuid4())
    event_type = 'APPROVAL_APPROVED' if decision == 'APPROVE' else 'APPROVAL_REJECTED'
    dynamodb.put_item(
        TableName=settings.TABLE_NAME,
        Item={
            'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': f"EVENT#{now}#{event_id}"},
            'entityType': {'S': 'TIMELINE_EVENT'}, 'eventType': {'S': event_type},
            'incidentId': {'S': incident_id}, 'timestamp': {'S': now},
            'metadata': {'M': {
                'approvalRequestId': {'S': approval_id}, 'decision': {'S': decision},
                'approverSub': {'S': approver_sub}, 'approverUsername': {'S': approver_username}, 'decidedAt': {'S': now}
            }}
        }
    )
    
    return True
