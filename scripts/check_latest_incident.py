import boto3
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('recourse-development-incidents')

response = table.scan()
incidents = []

for item in response.get('Items', []):
    if item['SK'] == 'META':
        created_at = item.get('createdAt')
        if created_at:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) - created_dt < timedelta(minutes=30):
                incidents.append(item)

# Sort by newest
incidents.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

if not incidents:
    print("No recent incidents found.")
else:
    latest = incidents[0]
    print(f"Latest Incident: {latest['PK'].replace('INCIDENT#', '')}")
    print(f"Status: {latest.get('status')}")
    print(f"Stage: {latest.get('investigationStage')}")
    print(f"Evidence ID: {latest.get('evidenceId', 'None')}")

    evidence_id = latest.get('evidenceId')
    if evidence_id:
        ev_response = table.get_item(Key={'PK': latest['PK'], 'SK': f"EVIDENCE#{evidence_id}"})
        if 'Item' in ev_response:
            print(f"Evidence Item Found!")
            ev = ev_response['Item']
            print(f"Completeness: {ev.get('evidenceCompleteness')}")
            print(f"Score: {ev.get('signalScore')}")
            print(f"Level: {ev.get('signalLevel')}")
        else:
            print("Evidence Item NOT FOUND in Dynamo!")
