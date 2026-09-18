import boto3
import time
from datetime import datetime, timezone

dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
table_name = "recourse-development-incidents"

print("Waiting for new incident...")
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

while True:
    res = dynamodb.query(
        TableName=table_name,
        IndexName="GSI2",
        KeyConditionExpression="GSI2PK = :pk",
        ExpressionAttributeValues={":pk": {"S": "INCIDENTS"}},
        ScanIndexForward=False,
        Limit=1
    )
    items = res.get('Items', [])
    if items:
        created_at = items[0].get('createdAt', {}).get('S', '')
        status = items[0].get('status', {}).get('S', '')
        stage = items[0].get('investigationStage', {}).get('S', '')
        incident_id = items[0].get('PK', {}).get('S', '')
        if today in created_at:
            print(f"\rFound incident: {incident_id} | Status: {status} | Stage: {stage} | Created: {created_at}", end='')
            if status == "INVESTIGATING" and stage == "AGENT_COMPLETE":
                print("\n\nSUCCESS! Agent complete.")
                break
            if status == "COMPLETE":
                print("\n\nIncident is COMPLETE (or manual override).")
                break
    time.sleep(2)
