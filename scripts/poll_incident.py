import boto3
import json
import decimal
import sys
import time

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('recourse-development-incidents')

# Find newest incident
res = table.query(
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :pk',
    ExpressionAttributeValues={':pk': 'INCIDENTS'},
    ScanIndexForward=False,
    Limit=1
)
items = res.get('Items', [])
if not items:
    print("No incidents found")
    sys.exit(0)

incident_id = items[0]['incidentId']
meta = items[0]

print(f"Latest Incident: {incident_id}")
if meta.get('investigationStage') != 'EVIDENCE_READY':
    print(f"Status is {meta.get('status')}, Stage is {meta.get('investigationStage')}... waiting")
    sys.exit(0)

print("\n=== META ===")
print(json.dumps(meta, indent=2, cls=DecimalEncoder))

context_id = meta.get('contextId')
evidence_id = meta.get('evidenceId')

if evidence_id:
    ev_res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'EVIDENCE#{evidence_id}'})
    print("\n=== EVIDENCE ===")
    print(json.dumps(ev_res.get('Item', {}), indent=2, cls=DecimalEncoder))

print("\n=== TIMELINE ===")
tl_res = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
    ExpressionAttributeValues={":pk": f"INCIDENT#{incident_id}", ":sk": "EVENT#"}
)
for item in tl_res.get('Items', []):
    print(f"{item.get('eventType')} - {item.get('timestamp')}")
