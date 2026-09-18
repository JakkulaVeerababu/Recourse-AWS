import boto3
import json

ssm = boto3.client('ssm')
STATE_PARAMETER_NAME = '/recourse/demo/state'

print("Setting Demo Mode to ANOMALY...")

try:
    ssm.put_parameter(
        Name=STATE_PARAMETER_NAME,
        Value=json.dumps({"mode": "ANOMALY", "anomaly_start_time": None, "invocations": 0}),
        Type='String',
        Overwrite=True
    )
    print("Controlled anomaly requested.")
    print("Safety duration: 120 seconds.")
    print("Invocation ceiling: 500.")
except Exception as e:
    print(f"Error updating state: {e}")
