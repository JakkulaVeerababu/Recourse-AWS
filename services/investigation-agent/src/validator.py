import logging
from typing import Dict, Any, List
from .models import InvestigationResult

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

def validate_investigation(result: InvestigationResult, evidence: Dict[str, Any], incident_id: str = "") -> InvestigationResult:
    # 1. Enforce human approval for non-NO_ACTION
    if result.proposedAction.actionType != "NO_ACTION" and not result.proposedAction.requiresHumanApproval:
        logger.warning("Agent proposed action without requiresHumanApproval=True. Forcing it to True.")
        result.proposedAction.requiresHumanApproval = True

    # 1b. Validate target resource relates to evidence/incident
    if result.proposedAction.actionType != "NO_ACTION" and result.proposedAction.targetResource:
        target = result.proposedAction.targetResource
        # Ensure it's not trying to target some arbitrary unrelated resource
        # Models often extrapolate ARNs, so we check if the last part of the ARN is in the evidence
        target_name = target.split(':')[-1]
        if target_name not in str(evidence) and target_name not in incident_id:
            logger.warning(f"Proposed target {target} not found in evidence or incident ID.")
            raise ValidationError(f"Target resource {target} does not match incident context.")

    # 2. Check citation validity (Does the referenced path exist in the evidence?)
    # Helper to traverse dict by dotted path
    def _path_exists(obj: Any, path: str) -> bool:
        keys = path.replace('[', '.').replace(']', '').split('.')
        current = obj
        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
                else:
                    return False
            return True
        except (KeyError, IndexError, ValueError, TypeError):
            return False

    for hypothesis in result.hypotheses:
        valid_refs = []
        for ref in hypothesis.supportingEvidence:
            if _path_exists(evidence, ref):
                valid_refs.append(ref)
            else:
                logger.warning(f"Citation {ref} not found in evidence.")
        
        hypothesis.supportingEvidence = valid_refs
                
        if not hypothesis.supportingEvidence:
            raise ValidationError(f"Hypothesis {hypothesis.hypothesisId} has no valid supporting evidence. You must cite exact paths from the provided JSON evidence schema (e.g. metricEvidence.invocations). Do not invent citations.")

    # 3. Deterministic Confidence Capping based on Completeness and Contradictions
    completeness = evidence.get('evidenceCompleteness', 'UNKNOWN')
    if completeness != 'COMPLETE' or result.contradictions or result.unknowns:
        if result.modelConfidence > 0.8:
            logger.warning("Capping model confidence to 0.80 due to incomplete evidence or contradictions.")
            result.modelConfidence = 0.80

    return result
