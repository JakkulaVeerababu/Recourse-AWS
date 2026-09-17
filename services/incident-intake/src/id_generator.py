import ulid

def generate_incident_id() -> str:
    """Generates a collision-resistant, sortable incident ID."""
    return f"INC-{ulid.new().str}"

def generate_event_id() -> str:
    """Generates a collision-resistant, sortable event ID."""
    return f"EVT-{ulid.new().str}"
