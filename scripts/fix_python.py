import os

services = ['incident-intake', 'context-collector', 'investigation-agent', 'policy-validator', 'remediation-executor', 'verifier', 'demo-load-generator']

for svc in services:
    path = os.path.join('services', svc, 'src', 'handler.py')
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace("extra={{'event': event}}", "extra={'event': event}")
    with open(path, 'w') as f:
        f.write(content)
