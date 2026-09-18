import pytest
from unittest.mock import patch, MagicMock

@patch('src.handler.get_policy_evaluation')
@patch('src.handler.get_incident_meta')
@patch('src.handler.get_evidence')
@patch('src.handler.get_investigation')
@patch('src.handler.evaluate_policy')
@patch('src.handler.save_policy_evaluation')
def test_handler_missing_input(
    mock_save, mock_eval, mock_inv, mock_evi, mock_meta, mock_get_eval
):
    from src.handler import handle
    res = handle({}, None)
    assert res['status'] == 'ERROR'

@patch('src.handler.get_policy_evaluation')
@patch('src.handler.get_incident_meta')
@patch('src.handler.get_evidence')
@patch('src.handler.get_investigation')
@patch('src.handler.evaluate_policy')
@patch('src.handler.save_policy_evaluation')
def test_handler_success(
    mock_save, mock_eval, mock_inv, mock_evi, mock_meta, mock_get_eval
):
    mock_get_eval.return_value = None
    mock_meta.return_value = {'severity': 'HIGH'}
    mock_evi.return_value = {'completeness': 'COMPLETE'}
    mock_inv.return_value = {'proposedAction': {'actionType': 'NO_ACTION'}}
    
    mock_eval.return_value = ("PERMIT", [], [])
    
    from src.handler import handle
    res = handle({
        'incident_id': 'INC-1',
        'evidence_id': 'EVD-1',
        'investigation_id': 'INV-1'
    }, None)
    
    assert res['decision'] == 'PERMIT'
    assert res['status'] == 'POLICY_COMPLETE'
