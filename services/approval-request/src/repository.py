import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple
from .config import dynamodb, settings

def generate_approval_id(incident_id: str, policy_eval_id: str, action: str, target: str) -> str:
    namespace = uuid.NAMESPACE_OID
    name = f"{incident_id}::{policy_eval_id}::{action}::{target}"
    return f"APR-{uuid.uuid5(namespace, name)}"

def create_approval_request(incident_id: str, payload: Dict[str, Any], encrypted_token: str) -> Tuple[str, str]:
    policy_eval_id = payload.get('policy_evaluation_id', 'UNKNOWN')
    investigation_id = payload.get('investigation_id', 'UNKNOWN')
    action = payload.get('proposedAction', {}).get('actionType', 'UNKNOWN')
    target = payload.get('proposedAction', {}).get('targetResource', 'UNKNOWN')
    
    approval_id = generate_approval_id(incident_id, policy_eval_id, action, target)
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.DEFAULT_EXPIRATION_MINUTES)
    
    requested_at = now.isoformat().replace('+00:00', 'Z')
    expires_at_iso = expires_at.isoformat().replace('+00:00', 'Z')
    
    try:
        dynamodb.put_item(
            TableName=settings.TABLE_NAME,
            Item={
                'PK': {'S': f"INCIDENT#{incident_id}"},
                'SK': {'S': f"APPROVAL#{approval_id}"},
                'entityType': {'S': 'APPROVAL_REQUEST'},
                'approvalRequestId': {'S': approval_id},
                'incidentId': {'S': incident_id},
                'investigationId': {'S': investigation_id},
                'policyEvaluationId': {'S': policy_eval_id},
                'actionType': {'S': action},
                'targetResource': {'S': target},
                'status': {'S': 'PENDING'},
                'requestedAt': {'S': requested_at},
                'expiresAt': {'S': expires_at_iso},
                'encryptedTaskToken': {'S': encrypted_token},
                'schemaVersion': {'S': '1.0'},
                'createdAt': {'S': requested_at},
                'updatedAt': {'S': requested_at}
            },
            ConditionExpression='attribute_not_exists(PK)'
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        pass

    dynamodb.update_item(
        TableName=settings.TABLE_NAME,
        Key={
            'PK': {'S': f"INCIDENT#{incident_id}"},
            'SK': {'S': 'META'}
        },
        UpdateExpression="SET #status = :newStatus, #investigationStage = :stage, #approvalStatus = :pending, #approvalRequestId = :aprId, #approvalRequestedAt = :reqAt, #updatedAt = :reqAt, #version = #version + :one",
        ExpressionAttributeNames={
            '#status': 'status',
            '#investigationStage': 'investigationStage',
            '#approvalStatus': 'approvalStatus',
            '#approvalRequestId': 'approvalRequestId',
            '#approvalRequestedAt': 'approvalRequestedAt',
            '#updatedAt': 'updatedAt',
            '#version': 'version'
        },
        ExpressionAttributeValues={
            ':newStatus': {'S': 'AWAITING_APPROVAL'},
            ':stage': {'S': 'APPROVAL_PENDING'},
            ':pending': {'S': 'PENDING'},
            ':aprId': {'S': approval_id},
            ':reqAt': {'S': requested_at},
            ':one': {'N': '1'}
        }
    )
    
    event_id = str(uuid.uuid4())
    dynamodb.put_item(
        TableName=settings.TABLE_NAME,
        Item={
            'PK': {'S': f"INCIDENT#{incident_id}"},
            'SK': {'S': f"EVENT#{requested_at}#{event_id}"},
            'entityType': {'S': 'TIMELINE_EVENT'},
            'eventType': {'S': 'APPROVAL_REQUESTED'},
            'incidentId': {'S': incident_id},
            'timestamp': {'S': requested_at},
            'metadata': {'M': {
                'approvalRequestId': {'S': approval_id},
                'actionType': {'S': action},
                'targetResource': {'S': target},
                'expiresAt': {'S': expires_at_iso}
            }}
        }
    )
    
    return approval_id, requested_at
