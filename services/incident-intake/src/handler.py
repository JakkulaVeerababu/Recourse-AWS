import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from src.models import DetectionEvent, IncidentMeta, IncidentEvent
from src.repository import IncidentRepository
from src.config import settings
from src.id_generator import generate_incident_id, generate_event_id

import os
import boto3

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

repo = IncidentRepository()
events_client = boto3.client('events')

def handle(event: Dict[str, Any], context) -> Dict[str, Any]:
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # EventBridge wrapper
        detail = event.get('detail', {})
        if not detail:
            return {"status": "ignored", "reason": "No detail in event"}
            
        detection = DetectionEvent.from_dict(detail)
    except Exception as e:
        logger.error(f"Failed to parse event: {e}")
        return {"status": "error", "reason": "INVALID_DETECTION_EVENT"}
        
    if detection.event_type == "ANOMALY_DETECTED":
        return _handle_anomaly_detected(detection)
    elif detection.event_type == "ALARM_RECOVERED":
        return _handle_alarm_recovered(detection)
    else:
        logger.warning(f"Unknown event_type: {detection.event_type}")
        return {"status": "ignored", "reason": "UNKNOWN_EVENT_TYPE"}

def _emit_incident_created(incident_id: str, detection: DetectionEvent):
    event_bus_name = os.environ.get("EVENT_BUS_NAME")
    if not event_bus_name:
        logger.warning("EVENT_BUS_NAME not set, skipping INCIDENT_CREATED emission")
        return
        
    payload = {
        "event_type": "INCIDENT_CREATED",
        "incident_id": incident_id,
        "status": "DETECTED",
        "resource_name": detection.resource_name,
        "resource_type": detection.resource_type,
        "severity": detection.severity,
        "created_at": detection.detected_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    try:
        events_client.put_events(
            Entries=[
                {
                    'Source': 'recourse.incidents',
                    'DetailType': 'Recourse Incident Created',
                    'Detail': json.dumps(payload),
                    'EventBusName': event_bus_name
                }
            ]
        )
        logger.info(f"Emitted INCIDENT_CREATED for {incident_id}")
    except Exception as e:
        logger.error(f"Failed to emit INCIDENT_CREATED to EventBridge: {e}")

def _handle_anomaly_detected(detection: DetectionEvent) -> Dict[str, Any]:
    idempotency_key = detection.event_id or detection.detection_id
    if not idempotency_key:
        return {"status": "error", "reason": "MISSING_IDEMPOTENCY_KEY"}
        
    incident_id = repo.get_idempotent_incident_id(idempotency_key)
    if incident_id:
        logger.info(f"Duplicate event detected. Returning existing incidentId: {incident_id}")
        return {"status": "success", "incidentId": incident_id, "note": "DUPLICATE_EVENT"}
        
    incident_id = generate_incident_id()
    timestamp = detection.detected_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    meta = IncidentMeta(
        PK=f"INCIDENT#{incident_id}",
        SK="META",
        GSI1PK=f"ALARM#{detection.alarm_name}",
        GSI1SK=timestamp,
        GSI2PK="INCIDENTS",
        GSI2SK=timestamp,
        incidentId=incident_id,
        status="DETECTED",
        severity=detection.severity,
        resourceName=detection.resource_name,
        resourceType=detection.resource_type,
        service=detection.service,
        region=detection.region,
        metric=detection.metric,
        baseline=detection.baseline,
        observed=detection.observed,
        deviationRatio=detection.deviation_ratio,
        alarmName=detection.alarm_name,
        alarmState=detection.alarm_state,
        sourceDetectionId=detection.detection_id,
        sourceEventId=detection.event_id,
        createdAt=timestamp,
        updatedAt=timestamp
    )
    
    event_id = generate_event_id()
    event_record = IncidentEvent(
        PK=f"INCIDENT#{incident_id}",
        SK=f"EVENT#{timestamp}#{event_id}",
        incidentId=incident_id,
        eventId=event_id,
        eventType="DETECTED",
        timestamp=timestamp,
        summary=f"Anomaly detected with {detection.deviation_ratio}x deviation",
        metadata=detection.model_dump(),
        sourceEventId=detection.event_id
    )
    
    ttl_timestamp = int((datetime.now(timezone.utc) + timedelta(days=settings.IDEMPOTENCY_TTL_DAYS)).timestamp())
    
    try:
        success = repo.create_incident_transaction(meta, event_record, idempotency_key, ttl_timestamp)
        if not success:
            # Condition check failed on PK/SK means it was inserted by another concurrent request
            existing_id = repo.get_idempotent_incident_id(idempotency_key)
            return {"status": "success", "incidentId": existing_id, "note": "DUPLICATE_EVENT_CONCURRENT"}
            
        logger.info(f"Created incident {incident_id}")
        _emit_incident_created(incident_id, detection)
        return {"status": "success", "incidentId": incident_id}
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        return {"status": "error", "reason": "DYNAMODB_WRITE_FAILED"}

def _handle_alarm_recovered(detection: DetectionEvent) -> Dict[str, Any]:
    incident = repo.find_latest_incident_for_alarm(detection.alarm_name)
    if not incident:
        logger.info("RECOVERY_WITHOUT_ACTIVE_INCIDENT")
        return {"status": "ignored", "reason": "RECOVERY_WITHOUT_ACTIVE_INCIDENT"}
        
    incident_id = incident.get('incidentId')
    timestamp = detection.timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event_id = generate_event_id()
    
    event_record = IncidentEvent(
        PK=f"INCIDENT#{incident_id}",
        SK=f"EVENT#{timestamp}#{event_id}",
        incidentId=incident_id,
        eventId=event_id,
        eventType="ALARM_RECOVERED",
        timestamp=timestamp,
        summary="CloudWatch alarm transitioned to OK",
        metadata=detection.model_dump(),
        sourceEventId=detection.event_id or ""
    )
    
    try:
        repo.append_recovery_event(incident, event_record)
        logger.info(f"Appended recovery event to incident {incident_id}")
        return {"status": "success", "incidentId": incident_id}
    except Exception as e:
        logger.error(f"Failed to append recovery event: {e}")
        return {"status": "error", "reason": "DYNAMODB_WRITE_FAILED"}
