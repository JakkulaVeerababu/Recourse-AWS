import boto3
import json
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('recourse-development-incidents')

# Query GSI2 for all incidents, newest first
r = table.query(
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :gsi2pk',
    ExpressionAttributeValues={':gsi2pk': 'INCIDENTS'},
    ScanIndexForward=False,
    Limit=5
)

print('=== Recent incidents ===')
for item in r['Items']:
    print(f"  incidentId={item.get('incidentId')}, status={item.get('status')}, createdAt={item.get('createdAt')}")
