import boto3
client = boto3.client('stepfunctions', region_name='ap-south-1')
res = client.get_execution_history(executionArn='arn:aws:states:ap-south-1:634005656298:execution:recourse-development-incident-orchestrator:INC-DISABLE-APPROVE-5')
events = res['events']
for e in events:
    if e['id'] == 52:
        print(e.get('taskSucceededEventDetails', {}).get('output'))
