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
incident_id = 'INC-01M2QHJ120PBMZZGRJF0G3V1YC'

# META
meta_res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': 'META'})
meta = meta_res.get('Item', {})
print("=== META ===")
print(json.dumps(meta, indent=2, cls=DecimalEncoder))

# CONTEXT
context_id = meta.get('contextId')
if context_id:
    ctx_res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'CONTEXT#{context_id}'})
    ctx = ctx_res.get('Item', {})
    print("\n=== CONTEXT ===")
    
    # Do not dump full logs, summarize
    metrics = ctx.get('metrics', {})
    print(f"Invocations datapoint count: len = {len(metrics.get('Invocations', []))}")
    print(f"Errors datapoint count: len = {len(metrics.get('Errors', []))}")
    print(f"Throttles datapoint count: len = {len(metrics.get('Throttles', []))}")
    print(f"Duration datapoint count: len = {len(metrics.get('Duration', []))}")
    
    # Just to see structure:
    if len(metrics.get('Invocations', [])) > 0:
        print(f"Invocations sample: {metrics.get('Invocations')[0]}")
    if len(metrics.get('Errors', [])) > 0:
        print(f"Errors sample: {metrics.get('Errors')[0]}")

    logs = ctx.get('logs', [])
    if isinstance(logs, dict):
        print(f"Log format: dict. Keys: {list(logs.keys())}")
        events = logs.get('events', [])
        print(f"log count: {len(events)}")
    elif isinstance(logs, list):
        print(f"Log format: list. log count: {len(logs)}")
    else:
        print(f"Log count (unknown structure): {logs}")

    print(f"logsTruncated: {ctx.get('logsTruncated')}")
    config = ctx.get('configuration', {})
    print(f"configuration keys: {list(config.keys())}")
    print(f"resource type: {ctx.get('resourceType')}")
    print(f"resource name: {ctx.get('resourceName')}")

# TIMELINE
timeline_res = table.query(
    KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
    ExpressionAttributeValues={
        ':pk': f'INCIDENT#{incident_id}',
        ':prefix': 'EVENT#'
    }
)
print("\n=== TIMELINE ===")
for item in timeline_res.get('Items', []):
    print(f"{item.get('eventType')} - {item.get('timestamp')} - {item.get('summary')}")
