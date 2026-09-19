import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

table = boto3.resource('dynamodb').Table('recourse-development-incidents')
resp = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
    ExpressionAttributeValues={":pk": "INCIDENT#INC-DISABLE-APPROVE-3", ":sk": "EVIDENCE#"}
)
for item in resp.get('Items', []):
    print(json.dumps(item, cls=DecimalEncoder, indent=2))
