import boto3
from datetime import datetime, timedelta, timezone
import logging
from src.config import BASELINE_PERIODS, METRIC_PERIOD_SECONDS, MIN_BASELINE_PERIODS, DETECTION_THRESHOLD

logger = logging.getLogger(__name__)

class CloudWatchMetrics:
    def __init__(self, client=None):
        self.client = client or boto3.client('cloudwatch')
        
    def get_invocation_metrics(self, function_name: str, end_time: datetime, periods: int) -> list[float]:
        """
        Fetches the Sum of Invocations for the given function over the last `periods` minutes.
        Expects end_time to be the time the alarm triggered (or near it).
        Returns a list of float values ordered by time.
        """
        start_time = end_time - timedelta(seconds=periods * METRIC_PERIOD_SECONDS)
        
        response = self.client.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[
                {'Name': 'FunctionName', 'Value': function_name}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=METRIC_PERIOD_SECONDS,
            Statistics=['Sum']
        )
        
        # In CloudWatch, if a period has absolutely no metrics, it might not be returned.
        # But for this workload we assume continuous data. We'll extract what we get.
        datapoints = response.get('Datapoints', [])
        # Sort by timestamp
        datapoints.sort(key=lambda x: x['Timestamp'])
        
        return [dp['Sum'] for dp in datapoints]

def calculate_baseline(values: list[float]) -> float | None:
    """
    Calculates the average of the provided metric values.
    Excludes any historical datapoints >= DETECTION_THRESHOLD.
    Requires at least MIN_BASELINE_PERIODS to return a valid baseline.
    """
    valid_values = [v for v in values if v < DETECTION_THRESHOLD]
    if len(valid_values) < MIN_BASELINE_PERIODS:
        return None
    return sum(valid_values) / len(valid_values)
