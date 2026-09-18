import logging
from typing import Dict, Any
from .config import settings
from .models import PolicyDecisionResult
from .repository import (
    get_incident_meta, 
    get_evidence, 
    get_investigation,
    get_policy_evaluation,
    save_policy_evaluation,
    generate_policy_evaluation_id
)
from .cedar_request import parse_canonical_facts
from .policy_engine import evaluate_policy
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handle(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    logger.info(f"Received event in {settings.SERVICE_NAME}", extra={'event': event})
    
    incident_id = event.get('incident_id')
    evidence_id = event.get('evidence_id')
    investigation_id = event.get('investigation_id')
    
    if not incident_id or not evidence_id or not investigation_id:
        return {'status': 'ERROR', 'error': 'Missing required input fields'}
        
    policy_eval_id = generate_policy_evaluation_id(incident_id, investigation_id, settings.POLICY_VERSION)
    
    # 1. Idempotency Check
    existing_eval = get_policy_evaluation(incident_id, policy_eval_id)
    if existing_eval:
        logger.info(f"Returning existing policy evaluation {policy_eval_id}")
        return PolicyDecisionResult(
            incident_id=incident_id,
            investigation_id=investigation_id,
            policy_evaluation_id=policy_eval_id,
            decision=existing_eval['decision'],
            status='POLICY_COMPLETE'
        ).model_dump()
        
    # 2. Load Canonical Facts
    incident_meta = get_incident_meta(incident_id)
    evidence = get_evidence(incident_id, evidence_id)
    investigation = get_investigation(incident_id, investigation_id)
    
    if not incident_meta or not evidence or not investigation:
        logger.error(f"Failed to load required facts from DynamoDB for {incident_id}")
        return {'status': 'ERROR', 'error': 'Failed to load canonical facts'}
        
    policy_context, principal, action, resource = parse_canonical_facts(incident_meta, evidence, investigation)
    
    # Determine recourseManaged
    recourse_managed = False
    evidence_resources = evidence.get('resources', [])
    for res in evidence_resources:
        if res.get('resourceArn', '') == resource.split('::"')[1].replace('"', ''):
            recourse_managed = bool(res.get('tags', {}).get('RecourseManaged', 'false').lower() == 'true')
            break
            
    context_dict = policy_context.model_dump()
            
    # 3. Evaluate Policy via Engine
    decision, determining_policies, errors = evaluate_policy(
        principal, 
        action, 
        resource, 
        context_dict, 
        recourse_managed
    )
    
    # 4. Persist Result
    save_policy_evaluation(
        incident_id=incident_id,
        evidence_id=evidence_id,
        investigation_id=investigation_id,
        policy_eval_id=policy_eval_id,
        decision=decision,
        determining_policies=determining_policies,
        errors=errors,
        context_snapshot=context_dict,
        principal=principal,
        action=action,
        resource=resource
    )
    
    return PolicyDecisionResult(
        incident_id=incident_id,
        investigation_id=investigation_id,
        policy_evaluation_id=policy_eval_id,
        decision=decision,
        status='POLICY_COMPLETE'
    ).model_dump()
