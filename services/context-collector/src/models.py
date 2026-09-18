from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class ContextResource:
    type: str
    name: str
    arn: str
    region: str

@dataclass
class ContextMetrics:
    invocations: List[dict] = field(default_factory=list)
    errors: List[dict] = field(default_factory=list)
    throttles: List[dict] = field(default_factory=list)
    duration: List[dict] = field(default_factory=list)

@dataclass
class ContextItem:
    context_id: str
    incident_id: str
    resource: ContextResource
    metrics: ContextMetrics
    configuration: Dict[str, Any]
    logs: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    collected_at: str
    schemaVersion: str = "1.0"
    
    def to_dict(self):
        return {
            "contextId": self.context_id,
            "incidentId": self.incident_id,
            "resource": {
                "type": self.resource.type,
                "name": self.resource.name,
                "arn": self.resource.arn,
                "region": self.resource.region
            },
            "metrics": {
                "invocations": self.metrics.invocations,
                "errors": self.metrics.errors,
                "throttles": self.metrics.throttles,
                "duration": self.metrics.duration
            },
            "configuration": self.configuration,
            "logs": self.logs,
            "metadata": self.metadata,
            "collectedAt": self.collected_at,
            "schemaVersion": self.schemaVersion,
            "entityType": "INCIDENT_CONTEXT"
        }
