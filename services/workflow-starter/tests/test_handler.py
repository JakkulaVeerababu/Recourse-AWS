import json
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import src.handler as handler

def test_missing_detail():
    result = handler.handle({}, None)
    assert result["status"] == "ignored"

def test_missing_incident_id():
    result = handler.handle({"detail": {}}, None)
    assert result["status"] == "ignored"

@patch('src.handler.sfn_client')
def test_success_path(mock_sfn):
    mock_sfn.start_execution.return_value = {"executionArn": "arn:test"}
    event = {"detail": {"incident_id": "INC-12345"}}
    
    result = handler.handle(event, None)
    
    assert result["status"] == "success"
    assert result["executionArn"] == "arn:test"
    mock_sfn.start_execution.assert_called_once_with(
        stateMachineArn=handler.settings.STATE_MACHINE_ARN,
        name="INC-12345",
        input=json.dumps(event)
    )

@patch('src.handler.sfn_client')
def test_execution_already_exists(mock_sfn):
    error_response = {'Error': {'Code': 'ExecutionAlreadyExists', 'Message': 'test'}}
    mock_sfn.start_execution.side_effect = ClientError(error_response, 'StartExecution')
    
    event = {"detail": {"incident_id": "INC-12345"}}
    
    result = handler.handle(event, None)
    
    assert result["status"] == "success"
    assert result.get("note") == "ExecutionAlreadyExists"
    
@patch('src.handler.sfn_client')
def test_other_client_error(mock_sfn):
    error_response = {'Error': {'Code': 'InternalFailure', 'Message': 'test'}}
    mock_sfn.start_execution.side_effect = ClientError(error_response, 'StartExecution')
    
    event = {"detail": {"incident_id": "INC-12345"}}
    
    result = handler.handle(event, None)
    
    assert result["status"] == "error"

def test_name_sanitization():
    # Test that invalid characters are replaced with underscores
    event = {"detail": {"incident_id": "INC-123#45/abc!"}}
    
    with patch('src.handler.sfn_client') as mock_sfn:
        mock_sfn.start_execution.return_value = {"executionArn": "arn:test"}
        handler.handle(event, None)
        
        args, kwargs = mock_sfn.start_execution.call_args
        assert kwargs["name"] == "INC-123_45_abc_"
