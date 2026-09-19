import sys
import boto3
import requests
import subprocess
import json
import time

def get_api_endpoint():
    api_client = boto3.client('apigateway')
    apis = api_client.get_rest_apis()['items']
    api = next((a for a in apis if 'approval-api' in a['name']), None)
    if not api:
        return None
    return f"https://{api['id']}.execute-api.ap-south-1.amazonaws.com/prod"

def main(incident_id):
    endpoint = get_api_endpoint()
    if not endpoint:
        print("Could not find API GW endpoint")
        sys.exit(1)
        
    print("Getting JWT Token...")
    token = subprocess.check_output([sys.executable, 'scripts/test_cognito_auth.py', '--get-token']).decode().strip()
    
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    url = f"{endpoint}/incidents/{incident_id}/approval"
    print(f"GET {url}")
    resp = requests.get(url, headers=headers)
    print(resp.status_code, resp.text)
    
    print(f"POST {url}")
    resp = requests.post(url, headers=headers, json={"decision": "APPROVE", "reason": "Looks good from CLI"})
    print(resp.status_code, resp.text)
    
    print("Waiting 5s for Step Functions to process callback...")
    time.sleep(5)
    
    ddb = boto3.client('dynamodb')
    meta = ddb.get_item(
        TableName='recourse-development-incidents',
        Key={'PK': {'S': f"INCIDENT#{incident_id}"}, 'SK': {'S': 'META'}}
    ).get('Item', {})
    
    print(f"Incident Status: {meta.get('status', {}).get('S')}")
    print(f"Investigation Stage: {meta.get('investigationStage', {}).get('S')}")
    print(f"Approval Status: {meta.get('approvalStatus', {}).get('S')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python phase9_approval_integration.py <incident_id>")
        sys.exit(1)
    main(sys.argv[1])
