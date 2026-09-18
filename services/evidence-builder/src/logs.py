import re
from typing import List, Dict, Any
from .models import LogSignal

def build_log_evidence(logs_data: Any) -> tuple:
    # logs_data can be a list of events or a dict like {'events': [...]} depending on context structure
    events = []
    if isinstance(logs_data, list):
        events = logs_data
    elif isinstance(logs_data, dict):
        events = logs_data.get('events', [])
        
    patterns = {
        "ERROR": r"ERROR",
        "Exception": r"Exception",
        "Task timed out": r"Task timed out",
        "AccessDenied": r"AccessDenied",
        "Throttle": r"Throttl",
        "Rate exceeded": r"Rate exceeded",
        "TooManyRequests": r"TooManyRequests",
        "OutOfMemory": r"OutOfMemory|MemoryError"
    }

    counts = {k: 0 for k in patterns}
    
    for event in events:
        msg = event.get('message', '')
        for k, p in patterns.items():
            if re.search(p, msg, re.IGNORECASE):
                counts[k] += 1

    signals = []
    
    if counts["Task timed out"] > 0:
        signals.append(LogSignal(pattern="Task timed out", count=counts["Task timed out"], signal="TIMEOUT_LOG_SIGNAL"))
    
    if counts["OutOfMemory"] > 0:
        signals.append(LogSignal(pattern="OutOfMemory", count=counts["OutOfMemory"], signal="MEMORY_LOG_SIGNAL"))
        
    if counts["AccessDenied"] > 0:
        signals.append(LogSignal(pattern="AccessDenied", count=counts["AccessDenied"], signal="ACCESS_DENIED_PRESENT"))
        
    if counts["Throttle"] > 0 or counts["Rate exceeded"] > 0 or counts["TooManyRequests"] > 0:
        c = counts["Throttle"] + counts["Rate exceeded"] + counts["TooManyRequests"]
        signals.append(LogSignal(pattern="Throttle/RateLimit", count=c, signal="THROTTLE_LOG_SIGNAL"))
        
    if counts["Exception"] > 0 or counts["ERROR"] > 0:
        c = counts["Exception"] + counts["ERROR"]
        signals.append(LogSignal(pattern="Error/Exception", count=c, signal="EXCEPTIONS_PRESENT"))
        
    if not signals:
        signals.append(LogSignal(pattern="*", count=0, signal="NO_EXCEPTION_SIGNAL"))

    # Convert counts to simple list for facts
    fact_patterns = [{"pattern": k, "count": v} for k, v in counts.items()]
    
    return fact_patterns, signals
