import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    lambda_client = boto3.client('lambda')
    
    function_name = 'recourse-development-investigation-agent'
    
    logger.info(f"Invoking {function_name} with ping event...")
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps({"ping": True})
    )
    
    payload = json.loads(response['Payload'].read().decode('utf-8'))
    logger.info(f"Response: {json.dumps(payload, indent=2)}")

if __name__ == '__main__':
    main()
