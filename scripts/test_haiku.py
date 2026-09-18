import boto3

runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
try:
    response = runtime.converse(
        modelId="us.anthropic.claude-3-haiku-20240307-v1:0",
        messages=[{"role": "user", "content": [{"text": "Hello, are you Haiku?"}]}]
    )
    print("SUCCESS converse!")
    print(response['output']['message']['content'][0]['text'])
except Exception as e:
    print(f"FAILED converse: {e}")

try:
    response = runtime.converse_stream(
        modelId="us.anthropic.claude-3-haiku-20240307-v1:0",
        messages=[{"role": "user", "content": [{"text": "Hello, are you Haiku?"}]}]
    )
    print("SUCCESS converse_stream!")
    for chunk in response['stream']:
        if 'contentBlockDelta' in chunk:
            print(chunk['contentBlockDelta']['delta']['text'], end='')
    print()
except Exception as e:
    print(f"FAILED converse_stream: {e}")
