import sys
import boto3

def main():
    try:
        runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        response = runtime.converse(
            modelId="amazon.nova-pro-v1:0",
            messages=[{"role": "user", "content": [{"text": "ping"}]}]
        )
        print("NOVA SUCCESS")
    except Exception as e:
        print(f"NOVA FAILED: {e}")

if __name__ == "__main__":
    main()
