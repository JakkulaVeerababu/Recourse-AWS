import logging
from typing import Dict, Any, Tuple
from .config import settings
import os

logger = logging.getLogger(__name__)

try:
    import cedarpy
    from cedarpy import is_authorized, AuthzResult, Decision
    CEDAR_AVAILABLE = True
except ImportError:
    CEDAR_AVAILABLE = False
    logger.error("cedarpy is not installed")

def _load_policy(path: str) -> str:
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load policy at {path}: {e}")
        return ""

# The Lambda runs with cwd as /var/task which corresponds to /asset-output in the builder
# and the policies directory is copied to /asset-output/policies
_base_path = os.environ.get('LAMBDA_TASK_ROOT', '.')
_SCHEMA_PATH = os.path.join(_base_path, 'policies/cedar/schema.cedarschema')
_INV_POLICY_PATH = os.path.join(_base_path, 'policies/cedar/policies/investigation-actions.cedar')
_SAFETY_POLICY_PATH = os.path.join(_base_path, 'policies/cedar/policies/resource-safety.cedar')

def evaluate_policy(
    principal: str, 
    action: str, 
    resource: str, 
    context: Dict[str, Any], 
    recourse_managed: bool
) -> Tuple[str, list, list]:
    
    if not CEDAR_AVAILABLE:
        return "FORBID", [], [{"message": "POLICY_ENGINE_ERROR: cedarpy missing"}]
        
    schema = _load_policy(_SCHEMA_PATH)
    inv_policy = _load_policy(_INV_POLICY_PATH)
    safety_policy = _load_policy(_SAFETY_POLICY_PATH)
    
    if not schema or (not inv_policy and not safety_policy):
        return "FORBID", [], [{"message": "POLICY_ENGINE_ERROR: Failed to load policies"}]
        
    policies = inv_policy + "\n" + safety_policy
    
    entities = [
        {
            "uid": {"type": principal.split('::"')[0], "id": principal.split('::"')[1].replace('"', '')},
            "attrs": {},
            "parents": []
        },
        {
            "uid": {"type": resource.split('::"')[0], "id": resource.split('::"')[1].replace('"', '')},
            "attrs": {
                "recourseManaged": recourse_managed
            },
            "parents": []
        }
    ]

    request = {
        "principal": principal,
        "action": action,
        "resource": resource,
        "context": context
    }
    
    try:
        result: AuthzResult = is_authorized(request, policies, entities, schema)
        
        decision = 'PERMIT' if result.decision == Decision.Allow else 'FORBID'
        
        determining_policies = [] # cedarpy might not expose this easily, or maybe result.diagnostics.reason has it
        
        errors = result.diagnostics.errors if hasattr(result.diagnostics, 'errors') else []
        if errors:
            logger.error(f"Cedar evaluation errors: {errors}")
            
        return decision, determining_policies, [{"message": e} for e in errors]

    except Exception as e:
        logger.error(f"Cedarpy Error: {e}")
        return "FORBID", [], [{"message": f"POLICY_ENGINE_ERROR: {str(e)}"}]
