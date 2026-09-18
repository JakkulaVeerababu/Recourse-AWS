import json
import subprocess
import os

cases = [
    {
        "Name": "NO_ACTION + unmanaged",
        "Action": 'Recourse::Action::"NO_ACTION"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": False,
        "Expected": "Allow"
    },
    {
        "Name": "MANUAL_INVESTIGATION + unmanaged",
        "Action": 'Recourse::Action::"MANUAL_INVESTIGATION"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": False,
        "Expected": "Allow"
    },
    {
        "Name": "REVIEW_CONFIGURATION + unmanaged",
        "Action": 'Recourse::Action::"REVIEW_CONFIGURATION"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": False,
        "Expected": "Allow"
    },
    {
        "Name": "DISABLE_EVENT_SOURCE + unmanaged",
        "Action": 'Recourse::Action::"DISABLE_EVENT_SOURCE"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": False,
        "Expected": "Deny"
    },
    {
        "Name": "REDUCE_INVOCATION_SOURCE + unmanaged",
        "Action": 'Recourse::Action::"REDUCE_INVOCATION_SOURCE"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": False,
        "Expected": "Deny"
    },
    {
        "Name": "DISABLE_EVENT_SOURCE + managed + target match + human approval + required severity",
        "Action": 'Recourse::Action::"DISABLE_EVENT_SOURCE"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": True,
        "Expected": "Allow"
    },
    {
        "Name": "unknown action",
        "Action": 'Recourse::Action::"DELETE_FUNCTION"',
        "Context": {"incidentSeverity": "HIGH", "evidenceCompleteness": "COMPLETE", "signalScore": 40, "proposedRisk": "LOW", "requiresHumanApproval": True, "targetMatchesIncident": True, "incidentStatus": "INVESTIGATING", "investigationStage": "AGENT_COMPLETE"},
        "Managed": True,
        "Expected": "Deny"
    }
]

with open("policies.cedar", "w") as out_f:
    with open("policies/cedar/policies/investigation-actions.cedar") as in_f:
        out_f.write(in_f.read() + "\n")
    with open("policies/cedar/policies/resource-safety.cedar") as in_f:
        out_f.write(in_f.read() + "\n")

for case in cases:
    req = {
        "principal": 'Recourse::Agent::"investigation-agent"',
        "action": case["Action"],
        "resource": 'Recourse::AWSResource::"target"',
        "context": case["Context"]
    }
    with open("request.json", "w") as f:
        json.dump(req, f, indent=2)
        
    entities = [
        {
            "uid": { "type": "Recourse::Agent", "id": "investigation-agent" },
            "attrs": {},
            "parents": []
        },
        {
            "uid": { "type": "Recourse::AWSResource", "id": "target" },
            "attrs": { "recourseManaged": case["Managed"] },
            "parents": []
        }
    ]
    with open("entities.json", "w") as f:
        json.dump(entities, f, indent=2)
        
    cmd = [
        ".\\cedar.exe", "authorize",
        "--schema", "policies/cedar/schema.cedarschema",
        "--policies", "policies.cedar",
        "--request-json", "request.json",
        "--entities", "entities.json"
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    output = res.stdout + res.stderr
    decision = "Allow" if "ALLOW" in output else ("Deny" if ("DENY" in output or "failed to parse request" in output) else f"Error: {output}")
    
    if decision == case["Expected"]:
        print(f"[OK] {case['Name']} -> {decision}")
    else:
        print(f"[FAIL] {case['Name']} -> Expected {case['Expected']}, got {decision}")
        print(output)
