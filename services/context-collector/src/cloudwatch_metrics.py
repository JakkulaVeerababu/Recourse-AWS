import boto3
import logging
from datetime import datetime, timedelta
from src.config import settings

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, client=None):
        self.client = client or boto3.client('cloudwatch')
        
    def collect(self, function_name: str, incident_time: datetime) -> dict:
        start_time = incident_time - timedelta(minutes=settings.METRICS_WINDOW_BEFORE_MINUTES)
        end_time = incident_time + timedelta(minutes=settings.METRICS_WINDOW_AFTER_MINUTES)
        
        metrics = {
            "invocations": self._get_metric(function_name, 'Invocations', 'Sum', start_time, end_time),
            "errors": self._get_metric(function_name, 'Errors', 'Sum', start_time, end_time),
            "throttles": self._get_metric(function_name, 'Throttles', 'Sum', start_time, end_time),
            "duration": self._get_metric(function_name, 'Duration', 'Average', start_time, end_time)
        }
        return metrics

    def _get_metric(self, function_name: str, metric_name: str, stat: str, start_time: datetime, end_time: datetime) -> list:
        try:
            response = self.client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName=metric_name,
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=[stat]
            )
            datapoints = response.get('Datapoints', [])
            datapoints.sort(key=lambda x: x['Timestamp'])
            return [
                {
                    "timestamp": dp['Timestamp'].isoformat().replace("+00:00", "Z"),
                    "value": dp[stat]
                }
                for dp in datapoints
            ]
        except Exception as e:
            logger.error(f"Failed to fetch {metric_name} metric: {e}")
            return []
