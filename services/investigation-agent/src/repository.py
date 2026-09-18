import boto3
import logging
import uuid
import datetime
from typing import Dict, Any
from .config import settings
from .models import InvestigationResult

logger = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(settings.INCIDENT_TABLE_NAME)

def generate_investigation_id(incident_id: str, evidence_id: str, model_version: str) -> str:
    namespace = uuid.NAMESPACE_DNS
    name = f"{incident_id}:{evidence_id}:{model_version}"
    return f"INV-{str(uuid.uuid5(namespace, name))}"

def get_investigation(incident_id: str, inv_id: str) -> bool:
    try:
        res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'INVESTIGATION#{inv_id}'})
        return 'Item' in res
    except Exception as e:
        logger.error(f"Error checking existing investigation: {e}")
        return False

def save_investigation(incident_id: str, context_id: str, evidence_id: str, result: InvestigationResult) -> str:
    inv_id = generate_investigation_id(incident_id, evidence_id, settings.PROMPT_VERSION)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    import json
    from decimal import Decimal
    
    # 1. Save the Investigation Item
    item = {
        'PK': f'INCIDENT#{incident_id}',
        'SK': f'INVESTIGATION#{inv_id}',
        'entityType': 'INCIDENT_INVESTIGATION',
        'investigationId': inv_id,
        'incidentId': incident_id,
        'contextId': context_id,
        'evidenceId': evidence_id,
        
        'modelProvider': 'AMAZON_BEDROCK',
        'modelId': settings.BEDROCK_MODEL_ID,
        'agentFramework': 'STRANDS',
        'promptVersion': settings.PROMPT_VERSION,
        
        'executiveSummary': result.executiveSummary,
        'hypotheses': [h.model_dump() for h in result.hypotheses],
        'contradictions': result.contradictions,
        'unknowns': result.unknowns,
        'proposedAction': result.proposedAction.model_dump(),
        'modelConfidence': result.modelConfidence,
        'leadingHypothesisId': result.leadingHypothesisId,
        
        'generatedAt': now,
        'schemaVersion': result.investigationVersion
    }
    
    item = json.loads(json.dumps(item), parse_float=Decimal)
    
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
        )
        logger.info(f"Persisted investigation {inv_id}")
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        logger.info(f"Investigation {inv_id} already exists, skipping put.")

    # 2. Append Timeline Event
    event_id = f"EVT-AGENT-{inv_id}"
    event_item = {
        'PK': f'INCIDENT#{incident_id}',
        'SK': f'EVENT#{now}#{event_id}',
        'incidentId': incident_id,
        'eventId': event_id,
        'eventType': 'AGENT_DIAGNOSIS',
        'timestamp': now,
        'summary': 'AI investigation completed and generated evidence-backed hypotheses.',
        'investigationId': inv_id,
        'modelProvider': 'AMAZON_BEDROCK',
        'agentFramework': 'STRANDS',
        'hypothesisCount': len(result.hypotheses),
        'modelConfidence': result.modelConfidence,
        'proposedActionType': result.proposedAction.actionType
    }
    
    event_item = json.loads(json.dumps(event_item), parse_float=Decimal)
    
    # Query for existing event idempotency using GSI if we wanted to be perfectly strict
    # but since the prompt specified deterministic SK or just one time event, we'll try to put it.
    # To keep SK deterministic for true idempotency, we can use the INV id as the SK suffix.
    # Wait, timeline SKs usually have timestamps for sorting. 
    # Let's just put the item. If the step functions retry happened, the timestamp is different,
    # so we'd get duplicate timeline events. Let's make SK completely deterministic for this event type.
    # SK: EVENT#AGENT_DIAGNOSIS#{inv_id} -> No, Step Functions requires sorting.
    # Let's use a conditional check or just let it insert. The prompt says: "Do not create multiple AGENT_DIAGNOSIS events on retries."
    
    # To enforce timeline idempotency, we will query if an AGENT_DIAGNOSIS exists for this inv_id
    res = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
        FilterExpression='investigationId = :inv',
        ExpressionAttributeValues={
            ':pk': f'INCIDENT#{incident_id}',
            ':sk_prefix': 'EVENT#',
            ':inv': inv_id
        }
    )
    if not res.get('Items'):
        table.put_item(Item=event_item)
        logger.info(f"Persisted timeline event {event_id}")
    else:
        logger.info(f"Timeline event for {inv_id} already exists, skipping put.")

    return inv_id
