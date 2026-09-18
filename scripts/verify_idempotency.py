import boto3
import json
from botocore.exceptions import ClientError

INCIDENT_ID = "INC-01M2QG9R3RPKHDRC2207M56EBC"

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('recourse-development-incidents')
sfn = boto3.client('stepfunctions', region_name='ap-south-1')
lam = boto3.client('lambda', region_name='ap-south-1')

# ===== STEP 6: Duplicate start proof =====
print("=" * 60)
print("STEP 6: Idempotency / Duplicate Start Proof")
print("=" * 60)

SM_ARN = 'arn:aws:states:ap-south-1:634005656298:stateMachine:recourse-development-incident-orchestrator'

# Count executions before replay
before = sfn.list_executions(stateMachineArn=SM_ARN, maxResults=50)
before_names = [e['name'] for e in before['executions']]
count_before = before_names.count(INCIDENT_ID)
print(f"  Execution count for {INCIDENT_ID} BEFORE replay: {count_before}")

# Replay INCIDENT_CREATED event to workflow-starter
event = {
    'version': '0',
    'id': 'replay-idempotency-test',
    'detail-type': 'Recourse Incident Created',
    'source': 'recourse.incidents',
    'account': '634005656298',
    'time': '2026-09-17T10:58:44Z',
    'region': 'ap-south-1',
    'detail': {
        'incident_id': INCIDENT_ID
    }
}

print(f"  Replaying INCIDENT_CREATED for {INCIDENT_ID} to workflow-starter...")
res = lam.invoke(
    FunctionName='recourse-development-workflow-starter',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)
payload = json.loads(res['Payload'].read().decode('utf-8'))
print(f"  workflow-starter response: {payload}")

# Count executions after replay
after = sfn.list_executions(stateMachineArn=SM_ARN, maxResults=50)
after_names = [e['name'] for e in after['executions']]
count_after = after_names.count(INCIDENT_ID)
print(f"  Execution count for {INCIDENT_ID} AFTER replay: {count_after}")
print(f"  Second execution created? {'YES - FAIL' if count_after > count_before else 'NO - PASS'}")

# ===== STEP 7: Timeline verification =====
print()
print("=" * 60)
print("STEP 7: Timeline Verification")
print("=" * 60)
r = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
    ExpressionAttributeValues={
        ':pk': f'INCIDENT#{INCIDENT_ID}',
        ':sk_prefix': 'EVENT#'
    }
)
events = sorted(r['Items'], key=lambda x: x['SK'])
print(f"  Total timeline events: {len(events)}")
for ev in events:
    print(f"    SK={ev.get('SK')}, eventType={ev.get('eventType')}")

# Count specific events
inv_started = sum(1 for e in events if e.get('eventType') == 'INVESTIGATION_STARTED')
ctx_collected = sum(1 for e in events if e.get('eventType') == 'CONTEXT_COLLECTED')
print()
print(f"  INVESTIGATION_STARTED count: {inv_started} (expected: 1)")
print(f"  CONTEXT_COLLECTED count: {ctx_collected} (expected: 1)")

# Count context items
ctx_r = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
    ExpressionAttributeValues={
        ':pk': f'INCIDENT#{INCIDENT_ID}',
        ':sk_prefix': 'CONTEXT#'
    }
)
print(f"  Context item count: {len(ctx_r['Items'])} (expected: 1)")
