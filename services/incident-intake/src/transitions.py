VALID_TRANSITIONS = {
    "DETECTED": ["INVESTIGATING"],
    "INVESTIGATING": ["VALIDATING", "MANUAL_REVIEW"],
    "VALIDATING": ["AWAITING_APPROVAL", "MANUAL_REVIEW"],
    "AWAITING_APPROVAL": ["APPROVED", "REJECTED"],
    "APPROVED": ["REMEDIATING"],
    "REMEDIATING": ["VERIFYING", "REMEDIATION_FAILED"],
    "VERIFYING": ["RESOLVED", "VERIFICATION_FAILED"],
    "RESOLVED": [],
    "REJECTED": [],
    "MANUAL_REVIEW": ["RESOLVED", "INVESTIGATING", "VALIDATING"],
    "REMEDIATION_FAILED": ["MANUAL_REVIEW"],
    "VERIFICATION_FAILED": ["MANUAL_REVIEW"]
}

def is_valid_transition(current_state: str, new_state: str) -> bool:
    """Checks if a state transition is valid based on the deterministic map."""
    allowed = VALID_TRANSITIONS.get(current_state, [])
    return new_state in allowed
