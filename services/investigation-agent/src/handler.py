import json
import logging
from .config import settings
from .agent import run_investigation
from .validator import validate_investigation, ValidationError
from .repository import save_investigation, get_investigation, generate_investigation_id
from .tools import get_evidence

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

def handle(event, context):
    logger.info(f'Received event in {settings.SERVICE_NAME}', extra={'event': event})
    
    incident_id = event.get('incident_id')
    context_id = event.get('context_id')
    evidence_id = event.get('evidence_id')
    
    if event.get('ping'):
        from strands import Agent
        from strands.models import BedrockModel
        model = BedrockModel(model_id=settings.BEDROCK_MODEL_ID, region_name=settings.BEDROCK_REGION, temperature=0.0)
        agent = Agent(name="ping", model=model)
        res = agent("Return exactly: RECOURSE_BEDROCK_OK")
        return {"status": "ok", "response": res.content if hasattr(res, 'content') else str(res)}
    
    if not incident_id or not context_id or not evidence_id:
        raise ValueError("Missing required fields: incident_id, context_id, evidence_id")
        
    logger.info(f"Starting investigation for Incident: {incident_id}, Evidence: {evidence_id}")
    
    # Idempotency check before invoking Bedrock
    expected_inv_id = generate_investigation_id(incident_id, evidence_id, settings.PROMPT_VERSION)
    if get_investigation(incident_id, expected_inv_id):
        logger.info(f"Deterministic investigation {expected_inv_id} already exists. Skipping Bedrock invocation.")
        return {
            'incident_id': incident_id,
            'investigation_id': expected_inv_id,
            'status': 'AGENT_COMPLETE'
        }
    
    # Pre-fetch evidence to pass to validator
    evidence_payload = get_evidence(incident_id, evidence_id)
    if 'error' in evidence_payload:
        raise ValueError(f"Could not load evidence {evidence_id}: {evidence_payload['error']}")

    try:
        raw_result = run_investigation(incident_id, context_id, evidence_id)
        logger.info(f"Agent finished generation. Validation started.")
        
        validated_result = validate_investigation(raw_result, evidence_payload, incident_id)
        logger.info(f"Validation successful.")
        
        inv_id = save_investigation(incident_id, context_id, evidence_id, validated_result)
        
        return {
            'incident_id': incident_id,
            'investigation_id': inv_id,
            'status': 'AGENT_COMPLETE'
        }

    except ValidationError as e:
        logger.error(f"Safety constraint violation: {e}")
        raise
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        raise
