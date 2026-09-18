import boto3
import json
import decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('recourse-development-incidents')
incident_id = 'INC-01M2QV04Y4HXE1VS3SQDRV3GE1'
evidence_id = 'EVD-d89cf859-28a6-5444-b524-af20803bb763'

# EVIDENCE
res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'EVIDENCE#{evidence_id}'})
evidence = res.get('Item', {})
print("=== EVIDENCE ===")
print(json.dumps(evidence, indent=2, cls=DecimalEncoder))

# Count evidence items
res_all = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
    ExpressionAttributeValues={":pk": f"INCIDENT#{incident_id}", ":sk": "EVIDENCE#"}
)
print(f"\nTotal Evidence Items: {len(res_all.get('Items', []))}")

# Count EVIDENCE_PREPARED events
events = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
    ExpressionAttributeValues={":pk": f"INCIDENT#{incident_id}", ":sk": "EVENT#"}
)
ep_count = sum(1 for e in events.get('Items', []) if e.get('eventType') == 'EVIDENCE_PREPARED')
print(f"Total EVIDENCE_PREPARED events: {ep_count}")
