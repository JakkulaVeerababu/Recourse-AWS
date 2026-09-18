import boto3
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from src.config import settings

logger = logging.getLogger(__name__)

REDACTION_PATTERNS = [
    (re.compile(r'AWS_ACCESS_KEY_ID=[\w]+', re.IGNORECASE), "AWS_ACCESS_KEY_ID=[REDACTED]"),
    (re.compile(r'AWS_SECRET_ACCESS_KEY=[\w+/]+', re.IGNORECASE), "AWS_SECRET_ACCESS_KEY=[REDACTED]"),
    (re.compile(r'(?i)authorization[\s\:\=]+bearer\s+[\w\-\.]+', re.IGNORECASE), "Authorization: Bearer [REDACTED]"),
    (re.compile(r'(?i)token[\s\=\:]+[\w\-\.]+', re.IGNORECASE), "token=[REDACTED]"),
    (re.compile(r'(?i)password[\s\=\:]+[\w]+', re.IGNORECASE), "password=[REDACTED]"),
    (re.compile(r'(?i)secret[\s\=\:]+[\w]+', re.IGNORECASE), "secret=[REDACTED]")
]

class LogsCollector:
    def __init__(self, client=None):
        self.client = client or boto3.client('logs')

    def collect(self, function_name: str, incident_time: datetime) -> Tuple[list, bool]:
        log_group_name = f"/aws/lambda/{function_name}"
        start_time = incident_time - timedelta(minutes=settings.LOGS_WINDOW_BEFORE_MINUTES)
        end_time = incident_time + timedelta(minutes=settings.LOGS_WINDOW_AFTER_MINUTES)
        
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        logs = []
        truncated = False
        
        try:
            response = self.client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_ts,
                endTime=end_ts,
                limit=settings.MAX_LOGS
            )
            
            events = response.get('events', [])
            if len(events) == settings.MAX_LOGS and 'nextToken' in response:
                truncated = True
                
            for event in events:
                message = event.get('message', '')
                
                # Truncate long messages
                if len(message) > settings.MAX_LOG_MESSAGE_LENGTH:
                    message = message[:settings.MAX_LOG_MESSAGE_LENGTH] + "... [TRUNCATED]"
                    truncated = True
                    
                # Redact
                for pattern, replacement in REDACTION_PATTERNS:
                    message = pattern.sub(replacement, message)
                    
                logs.append({
                    "timestamp": datetime.fromtimestamp(event['timestamp']/1000.0).isoformat(),
                    "message": message,
                    "logStreamName": event.get('logStreamName', '')
                })
                
        except self.client.exceptions.ResourceNotFoundException:
            logger.warning(f"Log group {log_group_name} not found.")
        except Exception as e:
            logger.error(f"Failed to fetch logs: {e}")
            
        return logs, truncated
