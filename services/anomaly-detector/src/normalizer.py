def extract_alarm_info(event: dict) -> dict:
    """
    Extracts relevant information from an EventBridge CloudWatch Alarm State Change event.
    """
    if event.get("source") != "aws.cloudwatch":
        raise ValueError("Event source must be aws.cloudwatch")
        
    detail_type = event.get("detail-type")
    if detail_type != "CloudWatch Alarm State Change":
        raise ValueError("Event detail-type must be CloudWatch Alarm State Change")
        
    detail = event.get("detail", {})
    alarm_name = detail.get("alarmName")
    if not alarm_name:
        raise ValueError("Missing alarmName in event detail")
        
    state = detail.get("state", {}).get("value")
    timestamp = detail.get("state", {}).get("timestamp", event.get("time"))
    
    configuration = detail.get("configuration", {})
    metrics = configuration.get("metrics", [])
    
    if not metrics:
        raise ValueError("Missing metrics configuration in alarm")
        
    metric_stat = metrics[0].get("metricStat", {})
    metric_info = metric_stat.get("metric", {})
    namespace = metric_info.get("namespace")
    metric_name = metric_info.get("name")
    
    dimensions = metric_info.get("dimensions", {})
    resource_name = dimensions.get("FunctionName") if namespace == "AWS/Lambda" else None
    
    if not resource_name:
        raise ValueError("Could not determine FunctionName from dimensions")
        
    return {
        "alarm_name": alarm_name,
        "state": state,
        "timestamp": timestamp,
        "namespace": namespace,
        "metric_name": metric_name,
        "resource_name": resource_name,
        "region": event.get("region"),
        "event_id": event.get("id")
    }
