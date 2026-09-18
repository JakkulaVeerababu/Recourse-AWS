import os
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
import json
from decimal import Decimal

def _get_table():
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('INCIDENT_TABLE_NAME', 'recourse-development-incidents')
    return dynamodb.Table(table_name)

def get_incident_meta(incident_id: str) -> Optional[Dict[str, Any]]:
    table = _get_table()
    try:
        response = table.get_item(
            Key={
                'PK': f"INCIDENT#{incident_id}",
                'SK': 'META'
            }
        )
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting META for {incident_id}: {e}")
        return None

def get_context(incident_id: str, context_id: str) -> Optional[Dict[str, Any]]:
    table = _get_table()
    try:
        response = table.get_item(
            Key={
                'PK': f"INCIDENT#{incident_id}",
                'SK': f"CONTEXT#{context_id}"
            }
        )
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting CONTEXT {context_id} for {incident_id}: {e}")
        return None

def _float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_float_to_decimal(v) for v in obj]
    return obj

def save_evidence(evidence: Dict[str, Any]) -> bool:
    table = _get_table()
    
    # Ensure float to decimal conversion for DynamoDB
    evidence_item = _float_to_decimal(evidence)
    evidence_item['PK'] = f"INCIDENT#{evidence['incidentId']}"
    evidence_item['SK'] = f"EVIDENCE#{evidence['evidenceId']}"
    evidence_item['entityType'] = "INCIDENT_EVIDENCE"
    
    try:
        table.put_item(
            Item=evidence_item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)"
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Evidence {evidence['evidenceId']} already exists.")
            return True # Treat as idempotent success
        print(f"Error saving evidence: {e}")
        raise e
