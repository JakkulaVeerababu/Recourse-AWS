import pytest
from src.normalizer import extract_alarm_info

def test_extract_alarm_info_valid():
    event = {
        "id": "12345",
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "time": "2026-09-17T06:13:43Z",
        "region": "ap-south-1",
        "detail": {
            "alarmName": "my-alarm",
            "state": {
                "value": "ALARM",
                "timestamp": "2026-09-17T06:13:43.000+0000"
            },
            "configuration": {
                "metrics": [
                    {
                        "metricStat": {
                            "metric": {
                                "namespace": "AWS/Lambda",
                                "name": "Invocations",
                                "dimensions": {
                                    "FunctionName": "my-function"
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
    
    info = extract_alarm_info(event)
    assert info["alarm_name"] == "my-alarm"
    assert info["state"] == "ALARM"
    assert info["timestamp"] == "2026-09-17T06:13:43.000+0000"
    assert info["namespace"] == "AWS/Lambda"
    assert info["metric_name"] == "Invocations"
    assert info["resource_name"] == "my-function"
    assert info["region"] == "ap-south-1"
    assert info["event_id"] == "12345"

def test_extract_alarm_info_invalid_source():
    event = {"source": "aws.ec2"}
    with pytest.raises(ValueError):
        extract_alarm_info(event)
