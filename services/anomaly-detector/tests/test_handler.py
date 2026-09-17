import pytest
from unittest.mock import patch, MagicMock
from src.handler import handle

@patch('src.handler.metrics_client')
def test_handle_ok_state(mock_metrics):
    event = {
        "id": "123",
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "region": "ap-south-1",
        "time": "2026-09-17T06:13:43Z",
        "detail": {
            "alarmName": "my-alarm",
            "state": {"value": "OK"},
            "configuration": {
                "metrics": [{"metricStat": {"metric": {"namespace": "AWS/Lambda", "name": "Invocations", "dimensions": {"FunctionName": "func"}}}}]
            }
        }
    }
    
    result = handle(event, None)
    assert result["status"] == "recovered"
    mock_metrics.get_invocation_metrics.assert_not_called()

@patch('src.handler.metrics_client')
def test_handle_alarm_state(mock_metrics):
    # Mock baseline values: returns valid baseline values
    mock_metrics.get_invocation_metrics.side_effect = [
        [20.0, 30.0, 25.0], # baseline
        [150.0, 100.0] # observed
    ]
    
    event = {
        "id": "123",
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "region": "ap-south-1",
        "time": "2026-09-17T06:13:43Z",
        "detail": {
            "alarmName": "my-alarm",
            "state": {"value": "ALARM", "timestamp": "2026-09-17T06:13:43.000+0000"},
            "configuration": {
                "metrics": [{"metricStat": {"metric": {"namespace": "AWS/Lambda", "name": "Invocations", "dimensions": {"FunctionName": "func"}}}}]
            }
        }
    }
    
    result = handle(event, None)
    assert result["status"] == "anomaly_detected"
    assert "detection_id" in result
    assert result["detection_id"].startswith("DET-")
    assert mock_metrics.get_invocation_metrics.call_count == 2

@patch('src.handler.metrics_client')
def test_handle_insufficient_baseline(mock_metrics):
    # Mock baseline values with too few normal datapoints
    mock_metrics.get_invocation_metrics.side_effect = [
        [20.0, 150.0, 140.0], # baseline (only one < 100)
        [250.0] # observed
    ]
    
    event = {
        "id": "123",
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "region": "ap-south-1",
        "time": "2026-09-17T06:13:43Z",
        "detail": {
            "alarmName": "my-alarm",
            "state": {"value": "ALARM", "timestamp": "2026-09-17T06:13:43.000+0000"},
            "configuration": {
                "metrics": [{"metricStat": {"metric": {"namespace": "AWS/Lambda", "name": "Invocations", "dimensions": {"FunctionName": "func"}}}}]
            }
        }
    }
    
    result = handle(event, None)
    assert result["status"] == "insufficient_data"
    assert "reason" in result
