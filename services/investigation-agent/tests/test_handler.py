import pytest
from unittest.mock import patch, MagicMock
from src.handler import handle
from src.models import InvestigationResult, ActionProposal, Hypothesis

def test_handler_missing_fields():
    with pytest.raises(ValueError, match="Missing required fields"):
        handle({}, None)

@patch('src.handler.get_evidence')
@patch('src.handler.run_investigation')
@patch('src.handler.validate_investigation')
@patch('src.handler.save_investigation')
def test_handler_success(mock_save, mock_validate, mock_run, mock_get_evidence):
    mock_get_evidence.return_value = {"some": "evidence"}
    
    mock_result = InvestigationResult(
        executiveSummary="Test",
        hypotheses=[
            Hypothesis(
                hypothesisId="HYP-1",
                title="T",
                description="D",
                likelihood="HIGH",
                confidence=0.9,
                supportingEvidence=["some"]
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
    mock_run.return_value = mock_result
    mock_validate.return_value = mock_result
    mock_save.return_value = "INV-123"

    response = handle({
        'incident_id': 'INC-1',
        'context_id': 'CTX-1',
        'evidence_id': 'EVD-1'
    }, None)

    assert response['incident_id'] == 'INC-1'
    assert response['investigation_id'] == 'INV-123'
    assert response['status'] == 'AGENT_COMPLETE'
