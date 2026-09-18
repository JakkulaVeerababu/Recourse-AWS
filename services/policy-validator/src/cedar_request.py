from typing import Dict, Any, Tuple
from .models import PolicyContext
import logging

logger = logging.getLogger(__name__)

def parse_canonical_facts(incident_meta: Dict[str, Any], evidence: Dict[str, Any], investigation: Dict[str, Any]) -> Tuple[PolicyContext, str, str, str]:
    severity = incident_meta.get('severity', 'LOW')
    incident_status = incident_meta.get('status', 'INVESTIGATING')
    investigation_stage = incident_meta.get('investigationStage', 'AGENT_COMPLETE')
    
    evidence_completeness = evidence.get('completeness', 'MINIMAL')
    signal_score = evidence.get('signalScore', 0)
    
    proposed_action = investigation.get('proposedAction', {})
    action_type = proposed_action.get('actionType', 'NO_ACTION')
    target_resource = proposed_action.get('targetResource', '')
    proposed_risk = proposed_action.get('risk', 'LOW')
    requires_human_approval = bool(proposed_action.get('requiresHumanApproval', True))
    
    model_confidence = float(investigation.get('modelConfidence', 0.0))
    
    # Target validation before Cedar
    target_matches_incident = False
    recourse_managed = False
    
    incident_resource = incident_meta.get('resourceArn', '')
    if not incident_resource:
        incident_resource = incident_meta.get('resourceId', '')
        
    if incident_resource and target_resource == incident_resource:
        target_matches_incident = True
        
    # Check explicitly if it matches resources in evidence
    evidence_resources = evidence.get('resources', [])
    for res in evidence_resources:
        arn = res.get('resourceArn', '')
        if arn == target_resource:
            target_matches_incident = True
            recourse_managed = bool(res.get('tags', {}).get('RecourseManaged', 'false').lower() == 'true')
            break
            
    # Default NO_ACTION targets self typically
    if action_type in ['NO_ACTION', 'MANUAL_INVESTIGATION']:
        target_matches_incident = True
        
    context = PolicyContext(
        incidentSeverity=severity,
        evidenceCompleteness=evidence_completeness,
        signalScore=int(signal_score),
        proposedRisk=proposed_risk,
        requiresHumanApproval=requires_human_approval,
        targetMatchesIncident=target_matches_incident,
        incidentStatus=incident_status,
        investigationStage=investigation_stage
    )
    
    # Model cedar request inputs
    principal = f'Recourse::Agent::"investigation-agent"'
    action = f'Recourse::Action::"{action_type}"'
    
    safe_target = target_resource.replace('"', '') if target_resource else 'unknown'
    resource = f'Recourse::AWSResource::"{safe_target}"'
    
    return context, principal, action, resource
