import boto3
import logging
from typing import Dict, Any, Optional
from strands import tool
from .config import settings

logger = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(settings.INCIDENT_TABLE_NAME)

@tool(
    name="get_incident",
    description="Fetch the incident metadata by incident_id.",
)
def get_incident(incident_id: str) -> Dict[str, Any]:
    try:
        res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': 'META'})
        return res.get('Item', {})
    except Exception as e:
        logger.error(f"Error fetching incident {incident_id}: {e}")
        return {"error": str(e)}

@tool(
    name="get_evidence",
    description="Fetch the deterministic evidence payload for an incident.",
)
def get_evidence(incident_id: str, evidence_id: str) -> Dict[str, Any]:
    try:
        res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'EVIDENCE#{evidence_id}'})
        item = res.get('Item', {})
        # Drop PK/SK/entityType for agent context to save tokens
        item.pop('PK', None)
        item.pop('SK', None)
        item.pop('entityType', None)
        return item
    except Exception as e:
        logger.error(f"Error fetching evidence {evidence_id}: {e}")
        return {"error": str(e)}
