from typing import List, Dict, Any
from .models import MetricEvidence, LogEvidence

def calculate_signal_score(metric_ev: MetricEvidence, log_ev: LogEvidence) -> tuple:
    score = 0

    # Invocation deviations
    inv_sig = metric_ev.invocations.signal
    if inv_sig == "SIGNIFICANT_INCREASE":
        score += 40
    elif inv_sig == "STRONG_INCREASE":
        score += 30
    elif inv_sig == "ELEVATED":
        score += 15

    # Errors
    err_sig = metric_ev.errors.signal
    if err_sig == "ERROR_SPIKE":
        score += 30
    elif err_sig == "ERRORS_PRESENT":
        score += 20

    # Throttling
    thr_sig = metric_ev.throttles.signal
    if thr_sig == "THROTTLING_SIGNIFICANT":
        score += 30
    elif thr_sig == "THROTTLING_PRESENT":
        score += 20
        
    # Duration (if peak > median significantly?) We didn't do deep duration analysis, but let's see.
    dur_fact = metric_ev.duration
    if dur_fact.medianDuration and dur_fact.peakDuration:
        if dur_fact.peakDuration > (dur_fact.medianDuration * 3):
            score += 10
            
    # Logs
    log_signals = [s['signal'] for s in log_ev.signals]
    if "EXCEPTIONS_PRESENT" in log_signals:
        score += 10
    if "TIMEOUT_LOG_SIGNAL" in log_signals:
        score += 10
    if "MEMORY_LOG_SIGNAL" in log_signals:
        score += 20
    if "ACCESS_DENIED_PRESENT" in log_signals:
        score += 15
        
    # Cap 0-100
    if score > 100:
        score = 100
    if score < 0:
        score = 0
        
    level = "LOW"
    if score >= 80:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 20:
        level = "MEDIUM"

    return score, level
