import boto3

cw = boto3.client('cloudwatch')
resp = cw.describe_alarms(AlarmNames=['recourse-development-demo-processor-invocation-anomaly'])
for alarm in resp['MetricAlarms']:
    print(f"Alarm {alarm['AlarmName']} is {alarm['StateValue']}")
