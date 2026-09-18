from decimal import Decimal
from typing import Dict, Any, List, Optional
from .models import MetricFact, ErrorFact, ThrottleFact, DurationFact

def analyze_invocations(points: List[Dict[str, Any]], incident_meta: Dict[str, Any]) -> MetricFact:
    # Use canonical baseline and observed if available in meta, else derive
    baseline = incident_meta.get('baseline')
    observed = incident_meta.get('observed')

    if baseline is None or observed is None:
        if not points:
            return MetricFact(metric="Invocations", status="INSUFFICIENT_DATA")
        # Fallback if meta doesn't have it
        values = [Decimal(str(p.get('value', 0))) for p in points]
        observed = max(values) if values else Decimal('0')
        baseline = Decimal('0') # We don't guess baseline here

    # Convert to decimal safely
    baseline = Decimal(str(baseline)) if baseline is not None else Decimal('0')
    observed = Decimal(str(observed)) if observed is not None else Decimal('0')

    ratio = Decimal('0')
    if baseline > 0:
        ratio = observed / baseline
    
    direction = "INCREASE" if observed > baseline else "NORMAL"
    if observed < baseline:
        direction = "DECREASE"

    signal = "NORMAL_RANGE"
    if ratio >= Decimal('5'):
        signal = "SIGNIFICANT_INCREASE"
    elif ratio >= Decimal('2'):
        signal = "STRONG_INCREASE"
    elif ratio >= Decimal('1.5'):
        signal = "ELEVATED"

    return MetricFact(
        metric="Invocations",
        status="COMPLETE",
        baseline=baseline,
        observed=observed,
        deviationRatio=ratio,
        direction=direction,
        signal=signal,
        details={"datapoints": len(points)}
    )

def analyze_errors(error_points: List[Dict[str, Any]], inv_points: List[Dict[str, Any]]) -> ErrorFact:
    values = [Decimal(str(p.get('value', 0))) for p in error_points] if error_points else []
    total = sum(values)

    inv_values = [Decimal(str(p.get('value', 0))) for p in inv_points] if inv_points else []
    total_inv = sum(inv_values)

    rate = (total / total_inv) if total_inv > 0 else Decimal('0')

    signal = "NO_ERROR_SPIKE"
    if total > 0:
        if total >= Decimal('10') or rate >= Decimal('0.1'):
            signal = "ERROR_SPIKE"
        else:
            signal = "ERRORS_PRESENT"

    return ErrorFact(
        status="COMPLETE",
        signal=signal,
        totalErrors=total,
        errorRate=rate
    )

def analyze_throttles(points: List[Dict[str, Any]]) -> ThrottleFact:
    values = [Decimal(str(p.get('value', 0))) for p in points] if points else []
    total = sum(values)

    signal = "NO_THROTTLING"
    if total > Decimal('50'):
        signal = "THROTTLING_SIGNIFICANT"
    elif total > 0:
        signal = "THROTTLING_PRESENT"

    return ThrottleFact(
        status="COMPLETE",
        signal=signal,
        totalThrottles=total
    )

def analyze_duration(points: List[Dict[str, Any]]) -> DurationFact:
    if not points:
        return DurationFact(status="INSUFFICIENT_DATA")
    
    values = [Decimal(str(p.get('value', 0))) for p in points]
    sorted_vals = sorted(values)
    
    if not sorted_vals:
        return DurationFact(status="INSUFFICIENT_DATA")

    peak = sorted_vals[-1]
    
    # Median
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2 == 0:
        median = (sorted_vals[mid - 1] + sorted_vals[mid]) / Decimal('2')
    else:
        median = sorted_vals[mid]

    signal = "DURATION_ANALYZED"
    
    return DurationFact(
        status="COMPLETE",
        signal=signal,
        medianDuration=median,
        peakDuration=peak
    )

def build_metric_evidence(context_metrics: Dict[str, Any], incident_meta: Dict[str, Any]) -> tuple:
    inv = context_metrics.get('invocations', context_metrics.get('Invocations', []))
    err = context_metrics.get('errors', context_metrics.get('Errors', []))
    thr = context_metrics.get('throttles', context_metrics.get('Throttles', []))
    dur = context_metrics.get('duration', context_metrics.get('Duration', []))

    inv_fact = analyze_invocations(inv, incident_meta)
    err_fact = analyze_errors(err, inv)
    thr_fact = analyze_throttles(thr)
    dur_fact = analyze_duration(dur)

    return inv_fact, err_fact, thr_fact, dur_fact
