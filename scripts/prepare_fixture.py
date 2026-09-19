import boto3
import json
import sys
import time

def prepare(incident_id, resource_type='AWS::Lambda::Function', resource_name='recourse-development-demo-processor'):
    ddb = boto3.client('dynamodb')
    print(f"Preparing {incident_id} for {resource_name}...")
    ddb.put_item(
        TableName='recourse-development-incidents',
        Item={
            'PK': {'S': f'INCIDENT#{incident_id}'},
            'SK': {'S': 'META'},
            'incidentId': {'S': incident_id},
            'status': {'S': 'DETECTED'},
            'severity': {'S': 'HIGH'},
            'resourceType': {'S': resource_type},
            'resourceName': {'S': resource_name},
            'createdAt': {'S': '2026-09-18T13:00:00Z'},
            'version': {'N': '1'}
        }
    )
    time.sleep(1)
    print("Triggering orchestrator...")
    boto3.client('stepfunctions').start_execution(
        stateMachineArn='arn:aws:states:ap-south-1:634005656298:stateMachine:recourse-development-incident-orchestrator',
        name=incident_id,
        input=json.dumps({"detail": {"incident_id": incident_id}})
    )
    print("Triggered! Waiting for AWAITING_APPROVAL...")
    
    for _ in range(30):
        time.sleep(5)
        item = ddb.get_item(
            TableName='recourse-development-incidents',
            Key={'PK': {'S': f'INCIDENT#{incident_id}'}, 'SK': {'S': 'META'}}
        ).get('Item', {})
        status = item.get('status', {}).get('S')
        print(f"Current status: {status}")
        if status == 'AWAITING_APPROVAL':
            print("Successfully reached AWAITING_APPROVAL!")
            return
        if status == 'REMEDIATED' or status == 'RESOLVED' or status == 'FAILED':
            print(f"Ended in {status}")
            return
            
    print("Timeout waiting for status.")

if __name__ == '__main__':
    res_type = sys.argv[2] if len(sys.argv) > 2 else 'AWS::Lambda::Function'
    res_name = sys.argv[3] if len(sys.argv) > 3 else 'recourse-development-demo-processor'
    prepare(sys.argv[1], res_type, res_name)
