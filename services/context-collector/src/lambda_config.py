import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LambdaConfigCollector:
    def __init__(self, client=None):
        self.client = client or boto3.client('lambda')

    def collect(self, function_name: str) -> Dict[str, Any]:
        try:
            response = self.client.get_function(FunctionName=function_name)
            config = response.get('Configuration', {})
            
            # Clean up environment variables (only keep keys)
            if 'Environment' in config and 'Variables' in config['Environment']:
                config['Environment']['Variables'] = {
                    k: "[REDACTED]" for k in config['Environment']['Variables'].keys()
                }
            
            # Remove bulky or non-essential fields for context size
            for key in ['CodeSha256', 'Role', 'VpcConfig']:
                config.pop(key, None)
                
            return {
                "FunctionName": config.get("FunctionName"),
                "Runtime": config.get("Runtime"),
                "MemorySize": config.get("MemorySize"),
                "Timeout": config.get("Timeout"),
                "LastModified": config.get("LastModified"),
                "State": config.get("State"),
                "Architectures": config.get("Architectures"),
                "EphemeralStorage": config.get("EphemeralStorage"),
                "TracingConfig": config.get("TracingConfig"),
                "EnvironmentKeys": list(config.get("Environment", {}).get("Variables", {}).keys())
            }
        except Exception as e:
            logger.error(f"Failed to fetch lambda configuration: {e}")
            return {}
