from typing import TypedDict, Optional

class AnomalyEvent(TypedDict):
    detection_id: str
    source: str
    alarm_name: str
    alarm_state: str
    service: str
    resource_name: str
    resource_type: str
    region: str
    metric: str
    period_seconds: int
    baseline: Optional[float]
    observed: Optional[float]
    deviation_ratio: Optional[float]
    severity: str
    detected_at: str
    event_id: str

class RecoveryEvent(TypedDict):
    event_type: str
    alarm_name: str
    resource_name: str
    state: str
    timestamp: str
    event_id: str
