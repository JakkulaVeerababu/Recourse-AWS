import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    "incident_id": "INC-01M2QV04Y4HXE1VS3SQDRV3GE1",
    "context_id": "CTX-76D18E6233F246CC839A674410"
}

response = lambda_client.invoke(
    FunctionName='recourse-development-evidence-builder',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read().decode('utf-8'))
print("Lambda Response:", json.dumps(result, indent=2))
