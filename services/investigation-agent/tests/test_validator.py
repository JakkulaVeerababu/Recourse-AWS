import pytest
from src.models import InvestigationResult, ActionProposal, Hypothesis
from src.validator import validate_investigation, ValidationError

def test_validator_enforces_human_approval():
    result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["some.valid.path"]
            )
        ],
        contradictions=[],
        unknowns=[],
        proposedAction=ActionProposal(
            actionType="DISABLE_EVENT_SOURCE",
            targetResource="arn:test",
            reason="test",
            expectedEffect="test",
            risk="HIGH",
            requiresHumanApproval=False # Should be forced to True
        ),
        modelConfidence=0.9
    )
    
    # We pass some mock evidence so it doesn't fail on missing citations yet
    validated = validate_investigation(result, {"some": {"valid": {"path": True}}, "target": "arn:test"}, "INC-1")
    assert validated.proposedAction.requiresHumanApproval is True

def test_validator_citation_checking():
    evidence = {
        "metricEvidence": {
            "invocations": {
                "observed": 100
            }
        }
    }
    
    result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["metricEvidence.invocations.observed", "invalid.path"]
            )
        ],
        contradictions=[],
        unknowns=[],
        proposedAction=ActionProposal(
            actionType="NO_ACTION",
            targetResource="none",
            reason="test",
            expectedEffect="test",
            risk="LOW",
            requiresHumanApproval=False
        ),
        modelConfidence=0.9
    )
    
    validated = validate_investigation(result, evidence)
    assert "metricEvidence.invocations.observed" in validated.hypotheses[0].supportingEvidence
    assert "invalid.path" not in validated.hypotheses[0].supportingEvidence

def test_validator_rejects_empty_citations():
    result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["invalid.path"]
            )
        ],
        contradictions=[],
        unknowns=[],
        proposedAction=ActionProposal(
            actionType="NO_ACTION",
            targetResource="none",
            reason="test",
            expectedEffect="test",
            risk="LOW",
            requiresHumanApproval=False
        ),
        modelConfidence=0.9
    )
    
    with pytest.raises(ValidationError):
        validate_investigation(result, {})

def test_confidence_capping():
    result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["metricEvidence.invocations"]
            )
        ],
        contradictions=["Some contradiction"],
        unknowns=[],
        proposedAction=ActionProposal(
            actionType="NO_ACTION",
            targetResource="none",
            reason="test",
            expectedEffect="test",
            risk="LOW",
            requiresHumanApproval=False
        ),
        modelConfidence=0.99
    )
    
    evidence = {
        "evidenceCompleteness": "COMPLETE",
        "metricEvidence": {"invocations": True}
    }
    validated = validate_investigation(result, evidence, "INC-1")
    assert validated.modelConfidence == 0.80

def test_validator_rejects_unrelated_target():
    result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["metricEvidence.invocations"]
            )
        ],
        contradictions=[],
        unknowns=[],
        proposedAction=ActionProposal(
            actionType="DISABLE_EVENT_SOURCE",
            targetResource="arn:unrelated",
            reason="test",
            expectedEffect="test",
            risk="LOW",
            requiresHumanApproval=True
        ),
        modelConfidence=0.99
    )
    
    evidence = {
        "metricEvidence": {"invocations": True},
        "target": "arn:related"
    }
    with pytest.raises(ValidationError, match="Target resource arn:unrelated does not match incident context."):
        validate_investigation(result, evidence, "INC-1")


