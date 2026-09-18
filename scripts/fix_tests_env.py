import os
import subprocess

services = [
    "anomaly-detector",
    "context-collector",
    "demo-load-generator",
    "demo-processor",
    "evidence-builder",
    "incident-intake",
    "investigation-agent",
    "policy-validator",
    "remediation-executor",
    "verifier",
    "workflow-starter"
]

env = os.environ.copy()
env['AWS_DEFAULT_REGION'] = 'ap-south-1'
env['STATE_MACHINE_ARN'] = 'arn:aws:states:ap-south-1:123456789012:stateMachine:recourse-development-incident-orchestrator'
env['TABLE_NAME'] = 'recourse-development-incidents'
env['INCIDENT_TABLE_NAME'] = 'recourse-development-incidents'
env['EVENT_BUS_NAME'] = 'recourse-development-events'

for svc in services:
    print(f"\n--- Testing {svc} ---")
    p = subprocess.run(["pytest", "tests/"], cwd=f"services/{svc}", env=env, capture_output=True, text=True)
    out = p.stdout
    # parse the summary line, e.g. "==== 5 passed in 0.12s ===="
    lines = out.split('\n')
    summary = lines[-2] if len(lines) >= 2 else "No output"
    print(summary)
    if p.returncode != 0:
        print(f"FAILED! Output:\n{out}")
