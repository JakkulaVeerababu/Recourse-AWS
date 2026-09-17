from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class DetectionEvent:
    event_type: str
    alarm_name: str
    resource_name: str
    detection_id: str = ""
    source: str = ""
    alarm_state: str = ""
    service: str = ""
    resource_type: str = ""
    region: str = ""
    metric: str = ""
    period_seconds: int = 0
    baseline: Optional[float] = None
    observed: Optional[float] = None
    deviation_ratio: Optional[float] = None
    severity: str = ""
    detected_at: str = ""
    event_id: str = ""
    timestamp: Optional[str] = None
    state: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            event_type=data.get("event_type", ""),
            alarm_name=data.get("alarm_name", ""),
            resource_name=data.get("resource_name", ""),
            detection_id=data.get("detection_id", ""),
            source=data.get("source", ""),
            alarm_state=data.get("alarm_state", ""),
            service=data.get("service", ""),
            resource_type=data.get("resource_type", ""),
            region=data.get("region", ""),
            metric=data.get("metric", ""),
            period_seconds=data.get("period_seconds", 0),
            baseline=data.get("baseline"),
            observed=data.get("observed"),
            deviation_ratio=data.get("deviation_ratio"),
            severity=data.get("severity", ""),
            detected_at=data.get("detected_at", ""),
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp"),
            state=data.get("state")
        )

    def model_dump(self, exclude_none=False) -> dict:
        d = self.__dict__
        if exclude_none:
            return {k: v for k, v in d.items() if v is not None}
        return d

@dataclass
class IncidentMeta:
    PK: str
    SK: str
    GSI1PK: str
    GSI1SK: str
    GSI2PK: str
    GSI2SK: str
    
    incidentId: str
    status: str
    severity: str
    
    resourceName: str
    resourceType: str
    service: str
    region: str
    metric: str
    
    alarmName: str
    alarmState: str
    
    sourceDetectionId: str
    sourceEventId: str
    
    createdAt: str
    updatedAt: str
    
    entityType: str = "INCIDENT"
    resourceArn: str = ""
    anomalyType: str = ""
    
    baseline: Optional[float] = None
    observed: Optional[float] = None
    deviationRatio: Optional[float] = None
    
    resolvedAt: Optional[str] = None
    version: int = 1
    schemaVersion: str = "1.0"
    
    def model_dump(self, exclude_none=False) -> dict:
        d = self.__dict__
        if exclude_none:
            return {k: v for k, v in d.items() if v is not None}
        return d

@dataclass
class IncidentEvent:
    PK: str
    SK: str
    
    incidentId: str
    eventId: str
    eventType: str
    timestamp: str
    summary: str
    sourceEventId: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    entityType: str = "INCIDENT_EVENT"
    actor: str = "SYSTEM"
    schemaVersion: str = "1.0"
    
    def model_dump(self, exclude_none=False) -> dict:
        d = self.__dict__
        if exclude_none:
            return {k: v for k, v in d.items() if v is not None}
        return d
