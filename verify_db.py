import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

client = boto3.client('dynamodb', region_name='ap-south-1')
table_name = 'recourse-development-incidents'
incident_id = 'INC-01M2Q54MQHTFHS7EGNK3WHNVHR'

print("=== 2. INSPECT EXISTING INCIDENT (GetItem) ===")
res = client.get_item(TableName=table_name, Key={'PK': {'S': f'INCIDENT#{incident_id}'}, 'SK': {'S': 'META'}})
print(json.dumps(res.get('Item', {}), indent=2, cls=DecimalEncoder))

print("\n=== 3. PROVE TIMELINE QUERY ===")
res = client.query(TableName=table_name, KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)', ExpressionAttributeValues={':pk': {'S': f'INCIDENT#{incident_id}'}, ':sk': {'S': 'EVENT#'}}, ScanIndexForward=True)
print(json.dumps(res.get('Items', []), indent=2, cls=DecimalEncoder))

print("\n=== 5. PROVE LIST INCIDENTS ===")
res = client.query(TableName=table_name, IndexName='GSI2', KeyConditionExpression='GSI2PK = :pk', ExpressionAttributeValues={':pk': {'S': 'INCIDENTS'}}, ScanIndexForward=False)
print(json.dumps(res.get('Items', []), indent=2, cls=DecimalEncoder))

print("\n=== 9. RECOVERY ASSOCIATION PROOF ===")
res = client.query(TableName=table_name, IndexName='GSI1', KeyConditionExpression='GSI1PK = :pk', ExpressionAttributeValues={':pk': {'S': 'ALARM#recourse-development-demo-processor-invocation-anomaly'}}, ScanIndexForward=False, Limit=1)
print(json.dumps(res.get('Items', []), indent=2, cls=DecimalEncoder))
