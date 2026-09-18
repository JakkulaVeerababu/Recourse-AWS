from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PolicyContext(BaseModel):
    incidentSeverity: str
    evidenceCompleteness: str
    signalScore: int
    proposedRisk: str
    requiresHumanApproval: bool
    targetMatchesIncident: bool
    incidentStatus: str
    investigationStage: str
    
class PolicyDecisionResult(BaseModel):
    incident_id: str
    investigation_id: str
    policy_evaluation_id: str
    decision: str
    status: str
