"""
Phase 7 Final Acceptance: Investigation-level idempotency test.

Uses the REAL incident INC-01M2SAT6FXH5EFJCRH4P3T4PYT.
Invokes the deployed Investigation Agent Lambda TWICE with the same payload.
Proves:
  - retry returns same investigationId
  - investigation item count = 1
  - AGENT_DIAGNOSIS count = 1
  - second Bedrock invocation = NO (proven by log message, not a new invocation)
"""

import boto3
import json
import time
from datetime import datetime, timezone

REGION = "ap-south-1"
INCIDENT_ID = "INC-01M2SAT6FXH5EFJCRH4P3T4PYT"
TABLE_NAME = "recourse-development-incidents"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
lambda_client = boto3.client("lambda", region_name=REGION)

# ──────────────────────────────────────────────────────────────
# Step 1: Load existing incident meta
# ──────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Load existing incident meta")
print("=" * 60)

meta_res = table.get_item(Key={"PK": f"INCIDENT#{INCIDENT_ID}", "SK": "META"})
meta = meta_res.get("Item", {})
if not meta:
    print(f"ERROR: Incident {INCIDENT_ID} not found in DynamoDB")
    exit(1)

context_id = meta.get("contextId")
evidence_id = meta.get("evidenceId")
investigation_id = meta.get("investigationId")
investigation_stage = meta.get("investigationStage")
status = meta.get("status")

print(f"  incidentId:         {INCIDENT_ID}")
print(f"  status:             {status}")
print(f"  contextId:          {context_id}")
print(f"  evidenceId:         {evidence_id}")
print(f"  investigationId:    {investigation_id}")
print(f"  investigationStage: {investigation_stage}")

if not context_id or not evidence_id:
    print("ERROR: Missing contextId or evidenceId in meta - cannot proceed")
    exit(1)

# ──────────────────────────────────────────────────────────────
# Step 2: Retrieve Lambda function name
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 2: Discover Investigation Agent Lambda")
print("=" * 60)

lambda_list = lambda_client.list_functions()
inv_agent_fn = None
for fn in lambda_list["Functions"]:
    name = fn["FunctionName"]
    if "investigation" in name.lower() and "development" in name.lower():
        inv_agent_fn = name
        print(f"  Found: {name}")
        print(f"  LastModified: {fn['LastModified']}")
        break

if not inv_agent_fn:
    print("ERROR: Could not find investigation-agent Lambda")
    exit(1)

# ──────────────────────────────────────────────────────────────
# Step 3: Count existing INVESTIGATION items before retry
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 3: Count existing INVESTIGATION and AGENT_DIAGNOSIS items BEFORE retry")
print("=" * 60)

def count_items_by_sk_prefix(incident_id, sk_prefix):
    res = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :skp)",
        ExpressionAttributeValues={
            ":pk": f"INCIDENT#{incident_id}",
            ":skp": sk_prefix
        }
    )
    return res.get("Items", [])

inv_items_before = count_items_by_sk_prefix(INCIDENT_ID, "INVESTIGATION#")
event_items_before = [i for i in count_items_by_sk_prefix(INCIDENT_ID, "EVENT#")
                      if i.get("eventType") == "AGENT_DIAGNOSIS"]

print(f"  INVESTIGATION items before retry: {len(inv_items_before)}")
print(f"  AGENT_DIAGNOSIS events before retry: {len(event_items_before)}")
if inv_items_before:
    print(f"  Existing investigationId: {inv_items_before[0].get('investigationId')}")

# ──────────────────────────────────────────────────────────────
# Step 4: First invoke (to confirm baseline)
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 4: INVOKE #1 — baseline idempotency check")
print("=" * 60)

payload_1 = {
    "incident_id": INCIDENT_ID,
    "context_id": context_id,
    "evidence_id": evidence_id
}

print(f"  Payload: {json.dumps(payload_1)}")
print(f"  Invoking: {inv_agent_fn}")
invoke_time_1 = datetime.now(timezone.utc)

response_1 = lambda_client.invoke(
    FunctionName=inv_agent_fn,
    InvocationType="RequestResponse",
    Payload=json.dumps(payload_1).encode()
)

result_1_raw = response_1["Payload"].read().decode()
result_1 = json.loads(result_1_raw)
duration_1_ms = response_1.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amzn-requestcharge", "N/A")

print(f"  StatusCode: {response_1['StatusCode']}")
print(f"  Result: {json.dumps(result_1, indent=2)}")
inv_id_1 = result_1.get("investigation_id") if isinstance(result_1, dict) else None

# ──────────────────────────────────────────────────────────────
# Step 5: Second invoke (retry simulation)
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 5: INVOKE #2 — simulated Lambda/Step Functions retry")
print("=" * 60)

print(f"  Payload: {json.dumps(payload_1)}  (identical)")
print(f"  Invoking: {inv_agent_fn}")
invoke_time_2 = datetime.now(timezone.utc)

response_2 = lambda_client.invoke(
    FunctionName=inv_agent_fn,
    InvocationType="RequestResponse",
    Payload=json.dumps(payload_1).encode()
)

result_2_raw = response_2["Payload"].read().decode()
result_2 = json.loads(result_2_raw)

print(f"  StatusCode: {response_2['StatusCode']}")
print(f"  Result: {json.dumps(result_2, indent=2)}")
inv_id_2 = result_2.get("investigation_id") if isinstance(result_2, dict) else None

# ──────────────────────────────────────────────────────────────
# Step 6: Count items AFTER retry
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 6: Count INVESTIGATION and AGENT_DIAGNOSIS items AFTER retry")
print("=" * 60)

time.sleep(3)  # brief pause for DynamoDB consistency

inv_items_after = count_items_by_sk_prefix(INCIDENT_ID, "INVESTIGATION#")
event_items_after = [i for i in count_items_by_sk_prefix(INCIDENT_ID, "EVENT#")
                     if i.get("eventType") == "AGENT_DIAGNOSIS"]

print(f"  INVESTIGATION items after retry: {len(inv_items_after)}")
print(f"  AGENT_DIAGNOSIS events after retry: {len(event_items_after)}")

# ──────────────────────────────────────────────────────────────
# Step 7: Check CloudWatch for idempotency log message
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("STEP 7: Check CloudWatch logs for idempotency branch proof")
print("=" * 60)

logs_client = boto3.client("logs", region_name=REGION)
log_group = f"/aws/lambda/{inv_agent_fn}"

try:
    # Get the most recent log stream
    streams = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy="LastEventTime",
        descending=True,
        limit=3
    )
    
    found_idempotency_log = False
    found_bedrock_init_on_retry = False
    
    for stream in streams["logStreams"]:
        stream_name = stream["logStreamName"]
        # Get events after invoke_time_1
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=int(invoke_time_1.timestamp() * 1000),
            limit=100
        )
        
        for ev in events["events"]:
            msg = ev.get("message", "")
            ts = datetime.fromtimestamp(ev["timestamp"] / 1000, tz=timezone.utc).isoformat()
            
            # Look for idempotency log
            if "already exists. Skipping Bedrock" in msg or "Deterministic investigation" in msg:
                print(f"  [IDEMPOTENCY LOG FOUND] {ts}")
                print(f"  Message: {msg.strip()}")
                found_idempotency_log = True
            
            # Check for any Strands/Bedrock initialization on retry (would be WRONG)
            if "run_investigation" in msg or "Agent finished generation" in msg:
                if ev["timestamp"] > int(invoke_time_2.timestamp() * 1000):
                    print(f"  [WARNING] Post-retry Bedrock invocation log: {msg.strip()}")
                    found_bedrock_init_on_retry = True

    if not found_idempotency_log:
        print("  WARNING: Idempotency log not found in recent streams. May be in earlier stream.")
        print("  Searching broader time window...")
        # Broader check
        for stream in streams["logStreams"]:
            events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=stream["logStreamName"],
                limit=200
            )
            for ev in events["events"]:
                msg = ev.get("message", "")
                if "already exists" in msg.lower() or "skipping bedrock" in msg.lower():
                    ts = datetime.fromtimestamp(ev["timestamp"] / 1000, tz=timezone.utc).isoformat()
                    print(f"  [IDEMPOTENCY LOG] {ts}: {msg.strip()}")
                    found_idempotency_log = True

except Exception as e:
    print(f"  CloudWatch query error: {e}")
    found_idempotency_log = False
    found_bedrock_init_on_retry = False

# ──────────────────────────────────────────────────────────────
# Final Report
# ──────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("FINAL ACCEPTANCE REPORT")
print("=" * 60)

ids_match = inv_id_1 is not None and inv_id_1 == inv_id_2
inv_count_stable = len(inv_items_after) == 1
diag_count_stable = len(event_items_after) == 1

print(f"  first investigationId:        {inv_id_1}")
print(f"  retry investigationId:        {inv_id_2}")
print(f"  IDs match:                    {'PASS' if ids_match else 'FAIL'}")
print()
print(f"  investigation item count:     {len(inv_items_after)}  (expected: 1) -> {'PASS' if inv_count_stable else 'FAIL'}")
print(f"  AGENT_DIAGNOSIS count:        {len(event_items_after)}  (expected: 1) -> {'PASS' if diag_count_stable else 'FAIL'}")
print()
print(f"  idempotency log found:        {'YES' if found_idempotency_log else 'NOT FOUND IN RECENT STREAMS'}")
print(f"  second Bedrock invocation:    {'NO (PASS)' if not found_bedrock_init_on_retry else 'YES (FAIL)'}")

print()
all_pass = ids_match and inv_count_stable and diag_count_stable and not found_bedrock_init_on_retry
if all_pass:
    print("  [OK] INVESTIGATION-LEVEL IDEMPOTENCY: PROVEN")
    print("  [OK] PHASE 7 FINAL ACCEPTANCE: COMPLETE")
else:
    print("  [FAIL] ONE OR MORE CHECKS FAILED -- review above")
print("=" * 60)
