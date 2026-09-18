import boto3
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from src.config import settings
from src.models import ContextItem

logger = logging.getLogger(__name__)

class ContextRepository:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = settings.INCIDENT_TABLE_NAME
        self.table = self.dynamodb.Table(self.table_name)
        self.client = boto3.client('dynamodb')

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.table.get_item(
                Key={
                    'PK': f"INCIDENT#{incident_id}",
                    'SK': "META"
                }
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get incident {incident_id}: {e}")
            return None

    def save_context(self, context_item: ContextItem) -> bool:
        pk = f"INCIDENT#{context_item.incident_id}"
        sk = f"CONTEXT#{context_item.context_id}"
        
        item = context_item.to_dict()
        item['PK'] = pk
        item['SK'] = sk
        
        try:
            serialized = self._serialize_item(item)
            self.client.put_item(
                TableName=self.table_name,
                Item=serialized,
                ConditionExpression='attribute_not_exists(PK) AND attribute_not_exists(SK)'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            raise e

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
