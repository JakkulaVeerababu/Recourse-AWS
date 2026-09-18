import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any

from src.repository import ContextRepository
from src.cloudwatch_metrics import MetricsCollector
from src.lambda_config import LambdaConfigCollector
from src.logs import LogsCollector
from src.resource_metadata import ResourceMetadataCollector
from src.models import ContextItem, ContextResource, ContextMetrics
from src.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

repo = ContextRepository()
metrics_collector = MetricsCollector()
config_collector = LambdaConfigCollector()
logs_collector = LogsCollector()
metadata_collector = ResourceMetadataCollector()

def handle(event: Dict[str, Any], context) -> Dict[str, Any]:
    logger.info(f"Received event: {json.dumps(event)}")
    
    incident_id = event.get('incident_id')
    if not incident_id:
        raise ValueError("Missing incident_id in input")
        
    # Fetch incident
    incident = repo.get_incident(incident_id)
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
        
    resource_type = incident.get('resourceType', 'AWS::Lambda::Function')
    if resource_type != 'AWS::Lambda::Function':
        return {
            "incident_id": incident_id,
            "status": "UNSUPPORTED_RESOURCE_TYPE",
            "reason": f"Resource type {resource_type} not supported by context collector"
        }
        
    resource_name = incident.get('resourceName')
    if not resource_name:
        raise ValueError("Missing resourceName in incident metadata")
        
    # Parse timestamp
    created_at_str = incident.get('createdAt')
    if not created_at_str:
        created_at_str = datetime.utcnow().isoformat() + "Z"
    
    try:
        incident_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except:
        incident_time = datetime.utcnow()
        
    # Check if resource is enrolled/managed (optional safety check)
    metadata = metadata_collector.collect(resource_name)
    tags = metadata.get('tags', {})
    if tags.get('RecourseManaged') != 'true' and 'demo-processor' not in resource_name:
        logger.warning(f"Resource {resource_name} is not enrolled with RecourseManaged=true")
        
    # Collect context
    metrics_data = metrics_collector.collect(resource_name, incident_time)
    config_data = config_collector.collect(resource_name)
    logs_data, truncated = logs_collector.collect(resource_name, incident_time)
    
    context_id = f"CTX-{uuid.uuid4().hex[:26].upper()}"
    
    metrics = ContextMetrics(
        invocations=metrics_data.get('invocations', []),
        errors=metrics_data.get('errors', []),
        throttles=metrics_data.get('throttles', []),
        duration=metrics_data.get('duration', [])
    )
    
    resource = ContextResource(
        type=resource_type,
        name=resource_name,
        arn=metadata.get('arn', ''),
        region=metadata.get('region', '')
    )
    
    collected_metadata = {
        "tags": metadata.get('tags', {}),
        "state": metadata.get('state'),
        "reserved_concurrency": metadata.get('reserved_concurrency'),
        "last_update_status": metadata.get('last_update_status'),
        "metricCounts": {k: len(v) for k, v in metrics_data.items()},
        "logCount": len(logs_data),
        "logsTruncated": truncated
    }
    
    context_item = ContextItem(
        context_id=context_id,
        incident_id=incident_id,
        resource=resource,
        metrics=metrics,
        configuration=config_data,
        logs=logs_data,
        metadata=collected_metadata,
        collected_at=datetime.utcnow().isoformat() + "Z"
    )
    
    # Save context
    repo.save_context(context_item)
    logger.info(f"Saved context {context_id} for incident {incident_id}")
    
    return {
        "incident_id": incident_id,
        "context_id": context_id,
        "status": "CONTEXT_COLLECTED"
    }
