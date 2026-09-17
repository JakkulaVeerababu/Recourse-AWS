import json
import logging
import uuid
import os
import boto3
from datetime import datetime, timedelta
from src.normalizer import extract_alarm_info
from src.metrics import CloudWatchMetrics, calculate_baseline
from src.severity import calculate_severity
from src.config import BASELINE_PERIODS, METRIC_PERIOD_SECONDS, ALARM_PERIOD_SECONDS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

metrics_client = CloudWatchMetrics()
events_client = boto3.client('events')

def handle(event, context):
    try:
        alarm_info = extract_alarm_info(event)
    except ValueError as e:
        logger.warning(f"Invalid event: {e}")
        return {"status": "ignored", "reason": str(e)}
        
    state = alarm_info["state"]
    alarm_name = alarm_info["alarm_name"]
    resource_name = alarm_info["resource_name"]
    event_id = alarm_info["event_id"]
    
    if state == "OK":
        recovery_event = {
            "event_type": "ALARM_RECOVERED",
            "alarm_name": alarm_name,
            "resource_name": resource_name,
            "state": "OK",
            "timestamp": alarm_info["timestamp"],
            "event_id": event_id
        }
        logger.info(json.dumps(recovery_event))
        emit_event(recovery_event)
        return {"status": "recovered"}
        
    elif state == "INSUFFICIENT_DATA":
        logger.info(f"Alarm {alarm_name} transitioned to INSUFFICIENT_DATA.")
        return {"status": "insufficient_data"}
        
    elif state == "ALARM":
        try:
            end_time = datetime.fromisoformat(alarm_info["timestamp"].replace("Z", "+00:00"))
        except:
            end_time = datetime.utcnow()
            
        # The breach period is the ALARM_PERIOD_SECONDS (e.g. 120s) before end_time
        baseline_end_time = end_time - timedelta(seconds=ALARM_PERIOD_SECONDS)
        
        # Fetch baseline metrics (e.g. 5 periods of 60s) before the breached window
        baseline_values = metrics_client.get_invocation_metrics(
            function_name=resource_name,
            end_time=baseline_end_time,
            periods=BASELINE_PERIODS
        )
        
        baseline = calculate_baseline(baseline_values)
        
        # If fewer than 3 valid periods exist, baseline_status = INSUFFICIENT_DATA
        if baseline is None:
            logger.warning("Insufficient valid baseline periods to calculate deviation.")
            return {"status": "insufficient_data", "reason": "Not enough normal baseline periods"}
            
        # Fetch observed values for the breached window (e.g. 2 periods of 60s)
        observed_periods = max(1, ALARM_PERIOD_SECONDS // METRIC_PERIOD_SECONDS)
        observed_values = metrics_client.get_invocation_metrics(
            function_name=resource_name,
            end_time=end_time,
            periods=observed_periods
        )
        # Take the maximum 60-second peak within the breached window
        observed = max(observed_values) if observed_values else None
        
        # Calculate deviation
        deviation_ratio = None
        if baseline > 0 and observed is not None:
            deviation_ratio = observed / baseline
            
        severity = calculate_severity(deviation_ratio)
        
        detection_id = f"DET-{uuid.uuid4().hex[:8].upper()}"
        
        anomaly_event = {
            "event_type": "ANOMALY_DETECTED",
            "detection_id": detection_id,
            "source": "cloudwatch",
            "alarm_name": alarm_name,
            "alarm_state": "ALARM",
            "service": "lambda",
            "resource_name": resource_name,
            "resource_type": "AWS::Lambda::Function",
            "region": alarm_info["region"],
            "metric": alarm_info["metric_name"],
            "period_seconds": METRIC_PERIOD_SECONDS,
            "baseline": float(f"{baseline:.1f}"),
            "observed": float(f"{observed:.1f}") if observed is not None else None,
            "deviation_ratio": float(f"{deviation_ratio:.2f}") if deviation_ratio is not None else None,
            "severity": severity,
            "detected_at": alarm_info["timestamp"],
            "event_id": event_id
        }
        
        logger.info(json.dumps(anomaly_event))
        emit_event(anomaly_event)
        return {"status": "anomaly_detected", "detection_id": detection_id}
        
    return {"status": "unknown_state"}

def emit_event(payload: dict):
    event_bus_name = os.environ.get("EVENT_BUS_NAME")
    if not event_bus_name:
        return
        
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'recourse.monitoring',
                    'DetailType': 'Recourse Anomaly Detection',
                    'Detail': json.dumps(payload),
                    'EventBusName': event_bus_name
                }
            ]
        )
    except Exception as e:
        logger.error(f"Failed to emit event to EventBridge: {e}")
