import boto3
import json
from decimal import Decimal

INCIDENT_ID = "INC-01M2QG9R3RPKHDRC2207M56EBC"
CONTEXT_ID = "CTX-B171271D00A34F3E9EEB4CE7F8"

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('recourse-development-incidents')

print("=" * 60)
print("STEP 8: Context Item Verification")
print("=" * 60)

r = table.get_item(Key={'PK': f'INCIDENT#{INCIDENT_ID}', 'SK': f'CONTEXT#{CONTEXT_ID}'})
ctx = r.get('Item', {})

if not ctx:
    print("  ERROR: Context item not found!")
else:
    print(f"  contextId: {ctx.get('contextId')}")
    
    # Check metrics
    metrics = ctx.get('metrics', {})
    invocations = metrics.get('Invocations', [])
    errors = metrics.get('Errors', [])
    throttles = metrics.get('Throttles', [])
    duration = metrics.get('Duration', [])
    
    print(f"  Invocations points: {len(invocations)}")
    print(f"  Errors points: {len(errors)}")
    print(f"  Throttles points: {len(throttles)}")
    print(f"  Duration points: {len(duration)}")
    
    # Check logs
    logs_data = ctx.get('logs', {})
    log_entries = logs_data.get('events', []) if isinstance(logs_data, dict) else logs_data
    logs_truncated = ctx.get('logsTruncated', ctx.get('logs', {}).get('truncated', False))
    print(f"  log count: {len(log_entries) if isinstance(log_entries, list) else 'N/A'}")
    print(f"  logsTruncated: {logs_truncated}")
    
    # Check environment
    env = ctx.get('lambdaConfig', {}).get('environment', {})
    env_vars = ctx.get('environment', {})
    print(f"  environment values persisted? {bool(env or env_vars)}")
    
    # Show all top-level keys
    print()
    print("  Context item top-level keys:")
    for k in sorted(ctx.keys()):
        v = ctx[k]
        if isinstance(v, (dict, list)):
            print(f"    {k}: [{type(v).__name__} with {len(v)} items]")
        else:
            print(f"    {k}: {str(v)[:80]}")
