import boto3
import json
from decimal import Decimal

INCIDENT_ID = "INC-01M2QG9R3RPKHDRC2207M56EBC"

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('recourse-development-incidents')
sfn = boto3.client('stepfunctions', region_name='ap-south-1')

# ===== STEP 4: META fields =====
print("=" * 60)
print("STEP 4: META Item Verification")
print("=" * 60)
r = table.get_item(Key={'PK': f'INCIDENT#{INCIDENT_ID}', 'SK': 'META'})
meta = r.get('Item', {})
fields = [
    'incidentId', 'status', 'version', 'investigationStage',
    'contextId', 'orchestrationExecutionArn', 'orchestrationStartedAt',
    'createdAt', 'updatedAt', 'alarmName', 'severity', 'observed', 'baseline'
]
for f in fields:
    print(f"  {f}: {meta.get(f, 'MISSING')}")

# ===== STEP 5: Step Functions execution =====
print()
print("=" * 60)
print("STEP 5: Step Functions Execution Verification")
print("=" * 60)
exec_arn = meta.get('orchestrationExecutionArn')
if exec_arn:
    exec_info = sfn.describe_execution(executionArn=exec_arn)
    print(f"  executionArn: {exec_info['executionArn']}")
    print(f"  executionName: {exec_info.get('name')}")
    print(f"  status: {exec_info['status']}")
    print(f"  startDate: {exec_info['startDate']}")
    print(f"  stopDate: {exec_info.get('stopDate', 'N/A')}")

    # State history
    hist = sfn.get_execution_history(executionArn=exec_arn, maxResults=50)
    print()
    print("  State history:")
    seen_states = []
    for e in hist['events']:
        if e['type'] == 'TaskStateEntered':
            name = e.get('stateEnteredEventDetails', {}).get('name', '')
            if name not in seen_states:
                seen_states.append(name)
                print(f"    - {name}")
else:
    print("  orchestrationExecutionArn not found in META")
