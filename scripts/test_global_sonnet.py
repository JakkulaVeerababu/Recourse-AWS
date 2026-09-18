import boto3

runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')
try:
    response = runtime.converse(
        modelId="global.anthropic.claude-sonnet-4-6",
        messages=[{"role": "user", "content": [{"text": "Hello, what model are you?"}]}]
    )
    print("SUCCESS!")
    print(response['output']['message']['content'][0]['text'])
except Exception as e:
    print(f"FAILED: {e}")
