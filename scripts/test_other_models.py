import boto3

models = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-micro-v1:0",
    "amazon.nova-lite-v1:0",
    "meta.llama3-8b-instruct-v1:0",
    "mistral.mistral-large-2402-v1:0"
]
regions = ['us-east-1', 'us-west-2', 'ap-south-1']

for region in regions:
    print(f"\n--- {region} ---")
    runtime = boto3.client('bedrock-runtime', region_name=region)
    for model_id in models:
        try:
            response = runtime.converse(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}]
            )
            print(f"SUCCESS: {model_id}")
        except Exception as e:
            print(f"FAILED {model_id}: {type(e).__name__} - {e}")
