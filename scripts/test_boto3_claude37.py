import boto3

runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')
try:
    response = runtime.converse_stream(
        modelId="apac.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=[{"role": "user", "content": [{"text": "say RECOURSE_BEDROCK_OK"}]}]
    )
    for chunk in response['stream']:
        print(chunk)
    print("BOTO3 TEST SUCCESS")
except Exception as e:
    print(f"BOTO3 TEST FAILED: {e}")
