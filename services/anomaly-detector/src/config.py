import os

DETECTION_THRESHOLD = float(os.environ.get('DETECTION_THRESHOLD', 100.0))
ALARM_PERIOD_SECONDS = int(os.environ.get('ALARM_PERIOD_SECONDS', 120))
METRIC_PERIOD_SECONDS = int(os.environ.get('METRIC_PERIOD_SECONDS', 60))
BASELINE_PERIODS = int(os.environ.get('BASELINE_PERIODS', 5))
MIN_BASELINE_PERIODS = int(os.environ.get('MIN_BASELINE_PERIODS', 3))

def validate_config():
    if DETECTION_THRESHOLD <= 0:
        raise ValueError("DETECTION_THRESHOLD must be > 0")
    if METRIC_PERIOD_SECONDS != 60:
        raise ValueError("METRIC_PERIOD_SECONDS must be 60")
    if BASELINE_PERIODS < MIN_BASELINE_PERIODS:
        raise ValueError("BASELINE_PERIODS must be >= MIN_BASELINE_PERIODS")
    if MIN_BASELINE_PERIODS <= 0:
        raise ValueError("MIN_BASELINE_PERIODS must be > 0")

validate_config()
