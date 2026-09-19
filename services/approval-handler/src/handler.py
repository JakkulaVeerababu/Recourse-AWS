import logging
import json
from typing import Dict, Any
from .auth import extract_approver_identity
from .models import ApprovalDecision
from pydantic import ValidationError
from .repository import get_approval_request, get_incident_meta, process_decision, decrypt_task_token, sfn

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _cors_headers() -> Dict[str, str]:
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    }

def handle(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
    
    parts = path.strip('/').split('/')
    if len(parts) != 3 or parts[0] != 'incidents' or parts[2] != 'approval':
        return {"statusCode": 404, "headers": _cors_headers(), "body": '{"error":"Not Found"}'}
        
    incident_id = parts[1]
    
    if method == 'OPTIONS':
        return {"statusCode": 204, "headers": _cors_headers()}
        
    if method not in ['GET', 'POST']:
        return {"statusCode": 405, "headers": _cors_headers(), "body": '{"error":"Method Not Allowed"}'}

    is_authorized, sub, username = extract_approver_identity(event)
    if not sub:
        return {"statusCode": 401, "headers": _cors_headers(), "body": '{"error":"Unauthorized"}'}
        
    meta = get_incident_meta(incident_id)
    if not meta:
        return {"statusCode": 404, "headers": _cors_headers(), "body": '{"error":"Incident Not Found"}'}
        
    approval_id = meta.get('approvalRequestId')
    if not approval_id:
        return {"statusCode": 404, "headers": _cors_headers(), "body": '{"error":"No approval request for this incident"}'}
        
    req = get_approval_request(incident_id, approval_id)
    if not req:
        return {"statusCode": 404, "headers": _cors_headers(), "body": '{"error":"Approval request not found"}'}

    if method == 'GET':
        safe_req = {
            "approvalRequestId": req.get("approvalRequestId"),
            "status": req.get("status"),
            "actionType": req.get("actionType"),
            "targetResource": req.get("targetResource"),
            "expiresAt": req.get("expiresAt")
        }
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps(safe_req)}

    if method == 'POST':
        if not is_authorized:
            return {"statusCode": 403, "headers": _cors_headers(), "body": '{"error":"Forbidden: Approver group required"}'}
            
        try:
            body = json.loads(event.get('body', '{}'))
            decision_model = ApprovalDecision(**body)
        except (json.JSONDecodeError, ValidationError) as e:
            return {"statusCode": 400, "headers": _cors_headers(), "body": '{"error":"Invalid payload"}'}
            
        # Policy recheck
        meta_decision = meta.get('policyDecision')
        if meta_decision != 'PERMIT':
            return {"statusCode": 403, "headers": _cors_headers(), "body": '{"error":"Cannot approve a FORBID decision"}'}
            
        if req.get('status') not in ['PENDING', 'APPROVED', 'REJECTED']:
             return {"statusCode": 409, "headers": _cors_headers(), "body": '{"error":"Request expired or invalid"}'}
             
        success = process_decision(
            incident_id, approval_id, decision_model.decision, decision_model.reason, sub, username
        )
        
        if not success:
            return {"statusCode": 409, "headers": _cors_headers(), "body": '{"error":"Conflict: Already decided differently"}'}
            
        try:
            task_token = decrypt_task_token(req.get('encryptedTaskToken'))
            callback_payload = {
                "approval_request_id": approval_id,
                "decision": decision_model.decision,
                "decided_at": req.get('updatedAt', ''),
                "approver_sub": sub
            }
            sfn.send_task_success(
                taskToken=task_token,
                output=json.dumps(callback_payload)
            )
        except Exception as e:
            logger.error(f"Failed to callback step functions: {str(e)}")
            
        return {"statusCode": 200, "headers": _cors_headers(), "body": json.dumps({"approvalRequestId": approval_id, "status": "APPROVED" if decision_model.decision == 'APPROVE' else "REJECTED"})}
