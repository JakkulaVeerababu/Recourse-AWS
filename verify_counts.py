import boto3
import json
from decimal import Decimal

client = boto3.client('dynamodb', region_name='ap-south-1')
table_name = 'recourse-development-incidents'
incident_id = 'INC-01M2Q54MQHTFHS7EGNK3WHNVHR'
event_id = '9d8f3921-b1df-8c69-4a9d-7744ab149480'

res_meta = client.get_item(TableName=table_name, Key={'PK': {'S': f'INCIDENT#{incident_id}'}, 'SK': {'S': 'META'}})
meta_item = res_meta.get('Item')
print(f"META count: {1 if meta_item else 0}")

res_timeline = client.query(TableName=table_name, KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)', ExpressionAttributeValues={':pk': {'S': f'INCIDENT#{incident_id}'}, ':sk': {'S': 'EVENT#'}}, ScanIndexForward=True)
timeline_items = res_timeline.get('Items', [])
detected_count = sum(1 for i in timeline_items if i.get('eventType', {}).get('S') == 'DETECTED')
recovered_count = sum(1 for i in timeline_items if i.get('eventType', {}).get('S') == 'ALARM_RECOVERED')
print(f"DETECTED count: {detected_count}")
print(f"ALARM_RECOVERED count: {recovered_count}")

res_idem = client.get_item(TableName=table_name, Key={'PK': {'S': f'IDEMPOTENCY#{event_id}'}, 'SK': {'S': 'DETECTION'}})
print(f"idempotency count: {1 if res_idem.get('Item') else 0}")

print("\nTIMELINE:")
for item in timeline_items:
    print(f"- {item['eventType']['S']} at {item['timestamp']['S']} (sourceEventId: {item['sourceEventId']['S']})")
