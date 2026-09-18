import boto3
import json
import sys
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def main():
    incident_id = sys.argv[1]
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    table = dynamodb.Table('recourse-development-incidents')
    
    # 1. Real Incident Meta
    print("==================================================")
    print("1. REAL INCIDENT META")
    print("==================================================")
    res = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': 'META'})
    meta = res.get('Item', {})
    print(json.dumps({
        'incidentId': meta.get('incidentId'),
        'status': meta.get('status'),
        'severity': meta.get('severity'),
        'contextId': meta.get('contextId'),
        'evidenceId': meta.get('evidenceId'),
        'investigationId': meta.get('investigationId'),
        'investigationStage': meta.get('investigationStage')
    }, indent=2, cls=DecimalEncoder))
    
    # 2. Real Investigation Item
    print("\n==================================================")
    print("2. REAL INVESTIGATION ITEM")
    print("==================================================")
    res_inv = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={':pk': f'INCIDENT#{incident_id}', ':sk': 'INVESTIGATION#'}
    )
    inv = res_inv.get('Items', [{}])[0] if res_inv.get('Items') else {}
    inv_id = inv.get('investigationId')
    print(json.dumps(inv, indent=2, cls=DecimalEncoder))
    
    # 3. Strict Citation Validation
    print("\n==================================================")
    print("3. STRICT CITATION VALIDATION")
    print("==================================================")
    ev_id = meta.get('evidenceId')
    res_ev = table.get_item(Key={'PK': f'INCIDENT#{incident_id}', 'SK': f'EVIDENCE#{ev_id}'})
    ev = res_ev.get('Item', {})
    
    total_refs = 0
    valid_refs = 0
    invalid_refs = 0
    synthetic_used = False
    
    def resolve_path(obj, path):
        parts = path.replace('][', '].[').replace('[', '.').replace(']', '').split('.')
        current = obj
        try:
            for part in parts:
                if not part: continue
                if isinstance(current, dict):
                    current = current[part]
                elif isinstance(current, list):
                    current = current[int(part)]
                else:
                    return False
            return True
        except (KeyError, IndexError, ValueError, TypeError):
            return False

    if inv_id and inv and ev:
        for hyp in inv.get('hypotheses', []):
            for ref in hyp.get('supportingEvidence', []):
                total_refs += 1
                if ref == ev_id or ref == "evidenceId":
                    synthetic_used = True
                    invalid_refs += 1
                else:
                    if resolve_path(ev.get('payload', {}), ref):
                        valid_refs += 1
                    else:
                        invalid_refs += 1
                        
    print(f"total references: {total_refs}")
    print(f"valid references: {valid_refs}")
    print(f"invalid references: {invalid_refs}")
    print(f"synthetic evidenceId fallback used? {'YES' if synthetic_used else 'NO'}")
    
    # 4. Timeline
    print("\n==================================================")
    print("6. TIMELINE")
    print("==================================================")
    r_time = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={':pk': f'INCIDENT#{incident_id}', ':sk': 'EVENT#'}
    )
    events = sorted(r_time.get('Items', []), key=lambda x: x['SK'])
    agent_diag_count = 0
    for e in events:
        etype = e.get('eventType')
        print(f"{etype} at {e.get('timestamp', e.get('SK'))}")
        if etype == 'AGENT_DIAGNOSIS':
            agent_diag_count += 1
            
    print(f"AGENT_DIAGNOSIS count = {agent_diag_count}")
    
    # 5. Step Functions
    print("\n==================================================")
    print("5. STEP FUNCTIONS")
    print("==================================================")
    sfn = boto3.client('stepfunctions', region_name='ap-south-1')
    sm_arn = 'arn:aws:states:ap-south-1:634005656298:stateMachine:recourse-development-incident-orchestrator'
    ex_arn = f"{sm_arn.replace('stateMachine', 'execution')}:{incident_id}"
    try:
        ex = sfn.describe_execution(executionArn=ex_arn)
        print(f"executionArn: {ex['executionArn']}")
        print(f"executionName: {ex['name']}")
        print(f"status: {ex['status']}")
        print(f"startDate: {ex['startDate']}")
        print(f"stopDate: {ex['stopDate']}")
        
        hist = sfn.get_execution_history(executionArn=ex_arn, maxResults=1000)
        redrives = 0 # No direct field, but checking if there's any ExecutionRedriven event
        for ev in hist['events']:
            if ev['type'] == 'ExecutionRedriven':
                redrives += 1
        print(f"redriveCount: {redrives}")
        
        # Output important states
        print("States entered:")
        for ev in hist['events']:
            if ev['type'] == 'TaskStateEntered' or ev['type'] == 'PassStateEntered' or ev['type'] == 'SucceedStateEntered':
                name = ev.get('stateEnteredEventDetails', {}).get('name')
                print(f"  - {name}")
    except Exception as e:
        print(f"SFN Error: {e}")
        
    print("\n==================================================")
    print("10. IAM FINAL CHECK (via Policy)")
    print("==================================================")
    iam = boto3.client('iam', region_name='ap-south-1')
    try:
        # Assuming role name starts with 'RecourseOrchestrationSt-InvestigationAgent'
        roles = iam.list_roles()['Roles']
        role = next((r for r in roles if 'InvestigationAgent' in r['RoleName']), None)
        if role:
            print(f"Role: {role['RoleName']}")
            policies = iam.list_attached_role_policies(RoleName=role['RoleName'])['AttachedPolicies']
            print(f"Attached Policies: {[p['PolicyName'] for p in policies]}")
            inline = iam.list_role_policies(RoleName=role['RoleName'])['PolicyNames']
            print(f"Inline Policies: {inline}")
            for p in inline:
                pol = iam.get_role_policy(RoleName=role['RoleName'], PolicyName=p)
                print(f"Policy Doc: {json.dumps(pol['PolicyDocument'], indent=2)}")
        else:
            print("InvestigationAgent role not found")
    except Exception as e:
        print(f"IAM Error: {e}")

if __name__ == '__main__':
    main()
