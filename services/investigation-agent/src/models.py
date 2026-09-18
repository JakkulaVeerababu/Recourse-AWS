from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ActionProposal(BaseModel):
    actionType: Literal[
        "NO_ACTION",
        "DISABLE_EVENT_SOURCE",
        "REDUCE_INVOCATION_SOURCE",
        "REVIEW_CONFIGURATION",
        "MANUAL_INVESTIGATION"
    ]
    targetResource: str = Field(description="The exact ARN, ID, or Name of the resource to target.")
    reason: str = Field(description="Reason for this action.")
    expectedEffect: str = Field(description="Expected effect of this action.")
    risk: Literal["LOW", "MEDIUM", "HIGH"]
    requiresHumanApproval: bool = Field(True, description="Must be true for any action other than NO_ACTION.")

class Hypothesis(BaseModel):
    hypothesisId: str = Field(description="Unique ID for this hypothesis (e.g. HYP-1).")
    title: str
    description: str
    likelihood: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: float = Field(ge=0.0, le=1.0)
    supportingEvidence: List[str] = Field(description="List of exact paths in the evidence object supporting this.")
    contradictingEvidence: List[str] = Field(default_factory=list)
    missingEvidence: List[str] = Field(default_factory=list)

class InvestigationResult(BaseModel):
    investigationVersion: str = "1.0"
    executiveSummary: str = Field(description="<= 500 characters summarizing the findings.", max_length=500)
    hypotheses: List[Hypothesis] = Field(min_length=1, max_length=5)
    leadingHypothesisId: Optional[str] = None
    contradictions: List[str] = Field(description="Important contradictions in evidence.")
    unknowns: List[str] = Field(description="Missing context or unknowns.")
    proposedAction: ActionProposal
    modelConfidence: float = Field(ge=0.0, le=1.0)
