import boto3
import json
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any

from src.config import settings
from src.models import IncidentMeta, IncidentEvent

logger = logging.getLogger(__name__)

class IncidentRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = settings.INCIDENT_TABLE_NAME
        self.table = self.dynamodb.Table(self.table_name)
        self.client = boto3.client('dynamodb')

    def create_incident_transaction(self, incident: IncidentMeta, event: IncidentEvent, idempotency_key: str, ttl_timestamp: int) -> bool:
        """
        Creates an incident, its first timeline event, and an idempotency record atomically.
        Returns True if successful, False if idempotency record already exists.
        """
        idempotency_pk = f"IDEMPOTENCY#{idempotency_key}"
        idempotency_sk = "DETECTION"
        
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        'Put': {
                            'TableName': self.table_name,
                            'Item': {
                                'PK': {'S': idempotency_pk},
                                'SK': {'S': idempotency_sk},
                                'incidentId': {'S': incident.incidentId},
                                'createdAt': {'S': incident.createdAt},
                                'ttl': {'N': str(ttl_timestamp)}
                            },
                            'ConditionExpression': 'attribute_not_exists(PK) AND attribute_not_exists(SK)'
                        }
                    },
                    {
                        'Put': {
                            'TableName': self.table_name,
                            'Item': self._serialize_item(incident.model_dump(exclude_none=True)),
                            'ConditionExpression': 'attribute_not_exists(PK)'
                        }
                    },
                    {
                        'Put': {
                            'TableName': self.table_name,
                            'Item': self._serialize_item(event.model_dump(exclude_none=True)),
                            'ConditionExpression': 'attribute_not_exists(PK) AND attribute_not_exists(SK)'
                        }
                    }
                ]
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'TransactionCanceledException':
                reasons = e.response.get('CancellationReasons', [])
                if reasons and reasons[0].get('Code') == 'ConditionalCheckFailed':
                    # Idempotency record exists
                    return False
                raise e
            raise e

    def get_idempotent_incident_id(self, idempotency_key: str) -> Optional[str]:
        idempotency_pk = f"IDEMPOTENCY#{idempotency_key}"
        try:
            response = self.table.get_item(
                Key={
                    'PK': idempotency_pk,
                    'SK': "DETECTION"
                }
            )
            return response.get('Item', {}).get('incidentId')
        except ClientError as e:
            logger.error(f"Failed to get idempotency record: {e}")
            return None

    def find_latest_incident_for_alarm(self, alarm_name: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f"ALARM#{alarm_name}"
                },
                ScanIndexForward=False,
                Limit=1
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Failed to query GSI1: {e}")
            return None

    def append_recovery_event(self, incident: Dict[str, Any], event: IncidentEvent) -> bool:
        """
        Appends a recovery event and updates the incident's alarmState to OK.
        """
        incident_pk = incident['PK']
        incident_sk = incident['SK']
        expected_version = incident.get('version', 1)
        new_version = expected_version + 1
        updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        'Update': {
                            'TableName': self.table_name,
                            'Key': {
                                'PK': {'S': incident_pk},
                                'SK': {'S': incident_sk}
                            },
                            'UpdateExpression': 'SET alarmState = :state, updatedAt = :updatedAt, version = :newVersion',
                            'ConditionExpression': 'version = :expectedVersion',
                            'ExpressionAttributeValues': {
                                ':state': {'S': 'OK'},
                                ':updatedAt': {'S': updated_at},
                                ':newVersion': {'N': str(new_version)},
                                ':expectedVersion': {'N': str(expected_version)}
                            }
                        }
                    },
                    {
                        'Put': {
                            'TableName': self.table_name,
                            'Item': self._serialize_item(event.model_dump(exclude_none=True)),
                            'ConditionExpression': 'attribute_not_exists(PK) AND attribute_not_exists(SK)'
                        }
                    }
                ]
            )
            return True
        except ClientError as e:
            logger.error(f"Transaction failed on append recovery: {e}")
            raise e

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"INCIDENT#{incident_id}",
                    'SK': "META"
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Failed to get incident: {e}")
            return None

    def get_incident_timeline(self, incident_id: str) -> list:
        try:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f"INCIDENT#{incident_id}",
                    ':sk_prefix': "EVENT#"
                },
                ScanIndexForward=True
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Failed to get timeline: {e}")
            return []

    def list_incidents(self) -> list:
        try:
            response = self.table.query(
                IndexName='GSI2',
                KeyConditionExpression='GSI2PK = :pk',
                ExpressionAttributeValues={
                    ':pk': "INCIDENTS"
                },
                ScanIndexForward=False
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Failed to list incidents: {e}")
            return []

    def _serialize_item(self, item: dict) -> dict:
        """Converts python types to DynamoDB typed dictionary"""
        def cast_floats(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: cast_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [cast_floats(i) for i in obj]
            return obj

        serializer = boto3.dynamodb.types.TypeSerializer()
        return {k: serializer.serialize(cast_floats(v)) for k, v in item.items()}
