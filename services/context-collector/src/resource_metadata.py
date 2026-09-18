import boto3
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ResourceMetadataCollector:
    def __init__(self, client=None):
        self.client = client or boto3.client('lambda')

    def collect(self, function_name: str) -> Dict[str, Any]:
        try:
            response = self.client.get_function(FunctionName=function_name)
            config = response.get('Configuration', {})
            arn = config.get('FunctionArn', '')
            
            # Fetch tags
            try:
                tags_response = self.client.list_tags(Resource=arn)
                tags = tags_response.get('Tags', {})
            except Exception as e:
                logger.error(f"Failed to fetch tags for {arn}: {e}")
                tags = {}
                
            # Fetch concurrency
            try:
                concurrency_response = self.client.get_function_concurrency(FunctionName=function_name)
                reserved_concurrency = concurrency_response.get('ReservedConcurrentExecutions', 'UNRESERVED')
            except Exception as e:
                logger.error(f"Failed to fetch concurrency for {function_name}: {e}")
                reserved_concurrency = 'UNKNOWN'
                
            return {
                "arn": arn,
                "name": function_name,
                "runtime": config.get('Runtime'),
                "region": arn.split(':')[3] if arn else '',
                "tags": tags,
                "state": config.get('State'),
                "reserved_concurrency": reserved_concurrency,
                "last_update_status": config.get('LastUpdateStatus')
            }
        except Exception as e:
            logger.error(f"Failed to fetch resource metadata: {e}")
            return {}
