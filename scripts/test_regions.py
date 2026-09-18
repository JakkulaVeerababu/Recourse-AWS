import boto3

regions = ['us-east-1', 'us-west-2', 'eu-central-1', 'ap-south-1']
models_to_test = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "eu.anthropic.claude-3-5-sonnet-20241022-v2:0"
]

for region in regions:
    print(f"\n--- Testing region {region} ---")
    runtime = boto3.client('bedrock-runtime', region_name=region)
    client = boto3.client('bedrock', region_name=region)
    
    # Let's list inference profiles in this region
    try:
        profiles = client.list_inference_profiles()['inferenceProfileSummaries']
        profiles = [p['inferenceProfileId'] for p in profiles if 'anthropic' in p['inferenceProfileId'].lower() and p['status'] == 'ACTIVE']
    except Exception:
        profiles = []
        
    for model_id in models_to_test + profiles:
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
            if "AccessDenied" in err or "ResourceNotFound" in err or "ValidationException" in err:
                # print(f"FAILED {model_id}: {type(e).__name__}")
                pass
            else:
                print(f"FAILED {model_id}: {e}")
