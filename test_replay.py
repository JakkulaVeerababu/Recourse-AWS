import boto3
import json

lambda_client = boto3.client('lambda', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('recourse-development-incidents')

def get_latest_incident():
    response = table.query(
        IndexName='status-index',
        KeyConditionExpression='#st = :st',
        ExpressionAttributeNames={'#st': 'status'},
        ExpressionAttributeValues={':st': 'INVESTIGATING'},
        Limit=1
    )
    if not response['Items']:
        response = table.query(
            IndexName='status-index',
            KeyConditionExpression='#st = :st',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={':st': 'DETECTED'},
            Limit=1
        )
    return response['Items'][0] if response['Items'] else None

def replay(incident_id):
    event = {
        'version': '0',
        'id': 'test-id-1234',
        'detail-type': 'Recourse.IncidentCreated',
        'source': 'recourse.incident-intake',
        'account': '634005656298',
        'time': '2026-09-17T10:00:00Z',
        'region': 'ap-south-1',
        'detail': {
            'incident_id': incident_id
        }
    }
    
    print(f'Replaying incident {incident_id} to workflow-starter...')
    res = lambda_client.invoke(
        FunctionName='recourse-development-workflow-starter',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    payload = json.loads(res['Payload'].read().decode('utf-8'))
    print(f'Response: {payload}')

incident_id = "INC-01M2QDFZF0QZTRYSG4BJ6BWXKH-2"
replay(incident_id)
