import boto3
import json

ssm = boto3.client('ssm')
STATE_PARAMETER_NAME = '/recourse/demo/state'

print(f"Setting Demo Mode to NORMAL...")

try:
    ssm.put_parameter(
        Name=STATE_PARAMETER_NAME,
        Value=json.dumps({"mode": "NORMAL", "anomaly_start_time": None, "invocations": 0}),
        Type='String',
        Overwrite=True
    )
    print("Success: Workload restored to Normal Mode.")
except Exception as e:
    print(f"Error updating state: {e}")
