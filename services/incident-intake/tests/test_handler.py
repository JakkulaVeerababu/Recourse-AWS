import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.handler import handle

@pytest.fixture
def anomaly_event():
    return {
        "detail": {
            "event_type": "ANOMALY_DETECTED",
            "detection_id": "DET-12345",
            "source": "cloudwatch",
            "alarm_name": "test-alarm",
            "alarm_state": "ALARM",
            "service": "lambda",
            "resource_name": "test-function",
            "resource_type": "AWS::Lambda::Function",
            "region": "ap-south-1",
            "metric": "Invocations",
            "period_seconds": 60,
            "baseline": 25.0,
            "observed": 150.0,
            "deviation_ratio": 6.0,
            "severity": "HIGH",
            "detected_at": "2026-09-17T06:54:44.948Z",
            "event_id": "EVT-SOURCE"
        }
    }

@pytest.fixture
def recovery_event():
    return {
        "detail": {
            "event_type": "ALARM_RECOVERED",
            "alarm_name": "test-alarm",
            "resource_name": "test-function",
            "state": "OK",
            "timestamp": "2026-09-17T06:56:44.948Z",
            "event_id": "EVT-RECOVERY"
        }
    }

@patch("src.handler.repo")
@patch("src.handler.generate_incident_id", return_value="INC-123")
@patch("src.handler.generate_event_id", return_value="EVT-123")
def test_handle_anomaly_detected_new(mock_event_id, mock_inc_id, mock_repo, anomaly_event):
    mock_repo.get_idempotent_incident_id.return_value = None
    mock_repo.create_incident_transaction.return_value = True
    
    response = handle(anomaly_event, None)
    
    assert response["status"] == "success"
    assert response["incidentId"] == "INC-123"
    mock_repo.create_incident_transaction.assert_called_once()

@patch("src.handler.repo")
def test_handle_anomaly_detected_duplicate(mock_repo, anomaly_event):
    mock_repo.get_idempotent_incident_id.return_value = "INC-EXISTING"
    
    response = handle(anomaly_event, None)
    
    assert response["status"] == "success"
    assert response["incidentId"] == "INC-EXISTING"
    assert response["note"] == "DUPLICATE_EVENT"
    mock_repo.create_incident_transaction.assert_not_called()

@patch("src.handler.repo")
@patch("src.handler.generate_incident_id", return_value="INC-123")
@patch("src.handler.generate_event_id", return_value="EVT-123")
def test_handle_anomaly_detected_concurrent_duplicate(mock_event_id, mock_inc_id, mock_repo, anomaly_event):
    # Initial check says it doesn't exist
    mock_repo.get_idempotent_incident_id.side_effect = [None, "INC-CONCURRENT"]
    # Transaction fails due to conditional check
    mock_repo.create_incident_transaction.return_value = False
    
    response = handle(anomaly_event, None)
    
    assert response["status"] == "success"
    assert response["incidentId"] == "INC-CONCURRENT"
    assert response["note"] == "DUPLICATE_EVENT_CONCURRENT"

@patch("src.handler.repo")
def test_handle_recovery_no_incident(mock_repo, recovery_event):
    mock_repo.find_latest_incident_for_alarm.return_value = None
    
    response = handle(recovery_event, None)
    
    assert response["status"] == "ignored"
    assert response["reason"] == "RECOVERY_WITHOUT_ACTIVE_INCIDENT"
    mock_repo.append_recovery_event.assert_not_called()

@patch("src.handler.repo")
@patch("src.handler.generate_event_id", return_value="EVT-456")
def test_handle_recovery_success(mock_event_id, mock_repo, recovery_event):
    mock_repo.find_latest_incident_for_alarm.return_value = {"incidentId": "INC-789", "PK": "INCIDENT#INC-789", "SK": "META", "version": 1}
    mock_repo.append_recovery_event.return_value = True
    
    response = handle(recovery_event, None)
    
    assert response["status"] == "success"
    assert response["incidentId"] == "INC-789"
    mock_repo.append_recovery_event.assert_called_once()
