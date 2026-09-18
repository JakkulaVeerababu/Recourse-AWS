import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    "incident_id": "INC-01M2SJXJ0S6HNXGZMCXAMPD6KS",
    "evidence_id": "EVD-6b77db5b-a82e-5f17-82c0-b926b3339d97",
    "investigation_id": "INV-f7513fc7-fe09-5bd0-84a2-e7d0d63c28b0"
}

print(f"Invoking policy validator with payload: {json.dumps(payload)}")

response = lambda_client.invoke(
    FunctionName='recourse-development-policy-validator',
    Payload=json.dumps(payload)
)

response_payload = json.loads(response['Payload'].read().decode('utf-8'))
print(f"Response: {json.dumps(response_payload, indent=2)}")

# Verify idempotency
expected_eval_id = "POL-c379edeb-5a33-5733-adad-76c51fb25242"
if response_payload.get("policy_evaluation_id") == expected_eval_id:
    print("Idempotency check PASSED")
else:
    print("Idempotency check FAILED")
