import boto3
import uuid
import datetime
import json
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from .config import settings
from decimal import Decimal

logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(settings.INCIDENT_TABLE_NAME)

def generate_policy_evaluation_id(incident_id: str, investigation_id: str, policy_version: str) -> str:
    namespace = uuid.NAMESPACE_DNS
    name = f"{incident_id}:{investigation_id}:{policy_version}"
    return f"POL-{str(uuid.uuid5(namespace, name))}"

def get_item(pk: str, sk: str) -> Optional[Dict[str, Any]]:
    try:
        response = table.get_item(Key={'PK': pk, 'SK': sk})
        return response.get('Item')
    except ClientError as e:
        logger.error(f"Error getting {sk} for {pk}: {e}")
        return None

def get_incident_meta(incident_id: str) -> Optional[Dict[str, Any]]:
    return get_item(f"INCIDENT#{incident_id}", "META")

def get_investigation(incident_id: str, investigation_id: str) -> Optional[Dict[str, Any]]:
    return get_item(f"INCIDENT#{incident_id}", f"INVESTIGATION#{investigation_id}")

def get_evidence(incident_id: str, evidence_id: str) -> Optional[Dict[str, Any]]:
    return get_item(f"INCIDENT#{incident_id}", f"EVIDENCE#{evidence_id}")

def get_policy_evaluation(incident_id: str, policy_eval_id: str) -> Optional[Dict[str, Any]]:
    return get_item(f"INCIDENT#{incident_id}", f"POLICY#{policy_eval_id}")

def _float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_float_to_decimal(v) for v in obj]
    return obj

def save_policy_evaluation(
    incident_id: str,
    evidence_id: str,
    investigation_id: str,
    policy_eval_id: str,
    decision: str,
    determining_policies: list,
    errors: list,
    context_snapshot: dict,
    principal: str,
    action: str,
    resource: str
) -> bool:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    item = {
        'PK': f'INCIDENT#{incident_id}',
        'SK': f'POLICY#{policy_eval_id}',
        'entityType': 'POLICY_EVALUATION',
        'policyEvaluationId': policy_eval_id,
        'incidentId': incident_id,
        'evidenceId': evidence_id,
        'investigationId': investigation_id,
        'principal': principal,
        'action': action,
        'resource': resource,
        'decision': decision,
        'determiningPolicies': determining_policies,
        'policyErrors': errors,
        'policyVersion': settings.POLICY_VERSION,
        'contextSnapshot': context_snapshot,
        'evaluatedAt': now,
        'schemaVersion': '1.0'
    }
    
    item = _float_to_decimal(item)

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
        )
        logger.info(f"Persisted policy evaluation {policy_eval_id}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.info(f"Policy evaluation {policy_eval_id} already exists, skipping put.")
        else:
            logger.error(f"Failed to persist policy evaluation: {e}")
            raise

    # 2. Append Timeline Event
    event_id = f"EVT-POL-{policy_eval_id}"
    event_item = {
        'PK': f'INCIDENT#{incident_id}',
        'SK': f'EVENT#{now}#{event_id}',
        'incidentId': incident_id,
        'eventId': event_id,
        'eventType': 'POLICY_EVALUATED',
        'timestamp': now,
        'summary': f"Cedar policy evaluation completed. Decision: {decision}",
        'policyEvaluationId': policy_eval_id,
        'decision': decision,
        'actionType': action,
        'policyVersion': settings.POLICY_VERSION
    }
    
    event_item = _float_to_decimal(event_item)
    
    res = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        FilterExpression='policyEvaluationId = :pid',
        ExpressionAttributeValues={
            ':pk': f'INCIDENT#{incident_id}',
            ':sk_prefix': 'EVENT#',
            ':pid': policy_eval_id
        }
    )
    if not res.get('Items'):
        table.put_item(Item=event_item)
        logger.info(f"Persisted timeline event {event_id}")
    else:
        logger.info(f"Timeline event for {policy_eval_id} already exists, skipping put.")

    return True
