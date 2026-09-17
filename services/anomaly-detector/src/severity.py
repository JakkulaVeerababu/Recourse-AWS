def calculate_severity(deviation_ratio: float | None) -> str:
    """
    Calculates severity deterministically based on deviation ratio.
    """
    if deviation_ratio is None:
        return "UNKNOWN"
        
    if deviation_ratio < 2.0:
        return "LOW"
    elif 2.0 <= deviation_ratio < 5.0:
        return "MEDIUM"
    elif 5.0 <= deviation_ratio < 10.0:
        return "HIGH"
    else:
        return "CRITICAL"
