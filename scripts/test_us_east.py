import boto3

regions = ['us-east-1', 'us-west-2', 'ap-south-1']
model_ids = [
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-7-sonnet-20250219-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0"
]

for region in regions:
    runtime = boto3.client('bedrock-runtime', region_name=region)
    for model_id in model_ids:
        try:
            response = runtime.converse_stream(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}]
            )
            for chunk in response['stream']:
                pass
            print(f"SUCCESS: {model_id} works in {region}!")
        except Exception as e:
            err = str(e)
            if "AccessDenied" not in err and "ValidationException" not in err and "ResourceNotFound" not in err:
                print(f"{region} - {model_id} FAILED: {err}")
