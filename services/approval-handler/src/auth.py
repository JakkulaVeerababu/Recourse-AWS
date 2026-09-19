from typing import Dict, Any, Tuple
from .config import settings

def extract_approver_identity(event: Dict[str, Any]) -> Tuple[bool, str, str]:
    claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    if not claims:
        claims = event.get('requestContext', {}).get('authorizer', {}).get('jwt', {}).get('claims', {})
    
    groups_claim = claims.get('cognito:groups', '')
    if isinstance(groups_claim, str):
        if groups_claim.startswith('[') and groups_claim.endswith(']'):
            import ast
            try:
                groups = ast.literal_eval(groups_claim)
            except:
                groups = []
        else:
            groups = [g.strip() for g in groups_claim.split(',')]
    elif isinstance(groups_claim, list):
        groups = groups_claim
    else:
        groups = []
    
    sub = claims.get('sub', '')
    username = claims.get('cognito:username', claims.get('username', sub))
    
    is_authorized = settings.ALLOWED_GROUP in groups
    return is_authorized, sub, username
