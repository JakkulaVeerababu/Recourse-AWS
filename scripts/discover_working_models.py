import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
client = boto3.client('bedrock', region_name='ap-south-1')
runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')

def discover_working_model():
    models = client.list_foundation_models()['modelSummaries']
    anthropic_models = [m['modelId'] for m in models if 'anthropic' in m['modelId'].lower() and m['modelLifecycle']['status'] == 'ACTIVE']
    
    # Also check inference profiles
    try:
        profiles = client.list_inference_profiles()['inferenceProfileSummaries']
        anthropic_models.extend([p['inferenceProfileId'] for p in profiles if 'anthropic' in p['inferenceProfileId'].lower() and p['status'] == 'ACTIVE'])
    except Exception as e:
        print(f"Failed to list profiles: {e}")

    for model_id in anthropic_models:
        print(f"Testing model: {model_id}")
        try:
            response = runtime.converse_stream(
                modelId=model_id,
                messages=[{"role": "user", "content": [{"text": "ping"}]}]
            )
            for chunk in response['stream']:
                pass
            print(f"SUCCESS: {model_id} works!")
            return model_id
        except Exception as e:
            print(f"FAILED {model_id}: {type(e).__name__} - {e}")
            
    print("No working Anthropic models found in ap-south-1")

if __name__ == "__main__":
    discover_working_model()
