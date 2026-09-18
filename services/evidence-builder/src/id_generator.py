import uuid

# Fixed namespace UUID for evidence IDs
EVIDENCE_NAMESPACE = uuid.UUID('e889d8d6-cf4e-4b41-bbdf-57bcce3b06df')

def generate_evidence_id(incident_id: str, context_id: str) -> str:
    """Generate a deterministic UUID5 based on incidentId and contextId."""
    name = f"{incident_id}:{context_id}"
    deterministic_uuid = uuid.uuid5(EVIDENCE_NAMESPACE, name)
    return f"EVD-{deterministic_uuid}"
