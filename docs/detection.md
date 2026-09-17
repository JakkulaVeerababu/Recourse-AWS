# Anomaly Detection Layer

The anomaly detection layer is responsible for translating operational metrics from CloudWatch into structured anomaly incidents.

## Telemetry & Baseline
The target workload (`demo-processor`) exhibits the following behavior in real AWS environments:
- **Baseline**: ~25 invocations/min
- **Controlled Anomaly**: ~250 invocations/min

## Thresholding
Based on the real baseline behavior, we use a deterministic CloudWatch Alarm threshold to separate normal from anomalous traffic.

- **Threshold**: 100 invocations / min
- **Alarm Metric**: `AWS/Lambda Invocations` for `recourse-development-demo-processor`
- **Period**: 60 seconds
- **Statistic**: Sum
- **Missing Data Treatment**: `NOT_BREACHING`

## Event Routing
When the CloudWatch Alarm breaches the threshold, it enters the `ALARM` state. When traffic returns to normal, it enters `OK`.
An EventBridge rule listens for `CloudWatch Alarm State Change` events and routes them to the `anomaly-detector` Lambda function.

## Severity Logic
The `anomaly-detector` uses a pure deterministic function to calculate the deviation ratio and determine severity:

- **Baseline Calculation**: Average of recent completed 1-minute metric periods (up to 5 periods, minimum of 3 required).
- **Deviation Ratio**: `Observed / Baseline`

**Severity Mapping:**
- `< 2x` -> `LOW`
- `2x <= deviation < 5x` -> `MEDIUM`
- `5x <= deviation < 10x` -> `HIGH`
- `>= 10x` -> `CRITICAL`

If insufficient baseline data exists, the severity is marked as `UNKNOWN`.

## ALARM and OK Transitions
- **ALARM**: The detector calculates the deviation, assigns severity, and produces a structured anomaly event.
- **OK**: The detector simply logs the recovery event, noting that the metric has returned to baseline levels.
