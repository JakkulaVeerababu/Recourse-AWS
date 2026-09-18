from typing import List, Dict, Any
from .models import MetricEvidence, LogEvidence, Correlation, SummaryFact

def build_correlations_and_summaries(
    metric_ev: MetricEvidence, 
    log_ev: LogEvidence,
    config_ev: Dict[str, Any]
) -> tuple:
    correlations = []
    summary_facts = []

    # Helper booleans
    inv_increase = metric_ev.invocations.direction == "INCREASE"
    inv_sig = metric_ev.invocations.signal in ["STRONG_INCREASE", "SIGNIFICANT_INCREASE"]
    err_spike = metric_ev.errors.signal == "ERROR_SPIKE"
    err_none = metric_ev.errors.signal == "NO_ERROR_SPIKE"
    thr_present = metric_ev.throttles.signal in ["THROTTLING_PRESENT", "THROTTLING_SIGNIFICANT"]
    
    # 1. Correlations
    if inv_sig and err_none:
        correlations.append(Correlation(
            type="TRAFFIC_INCREASE_WITHOUT_ERROR_SPIKE",
            statement="Invocations significantly increased AND Errors remain zero/near-zero."
        ))
    
    if inv_increase and thr_present:
        correlations.append(Correlation(
            type="TRAFFIC_INCREASE_WITH_THROTTLING",
            statement="Invocation increase coincided with throttling."
        ))

    # We don't have duration baseline reliably, so we won't assert latency increase blindly.

    # 2. Summary Facts
    if metric_ev.invocations.deviationRatio:
        summary_facts.append(SummaryFact(
            type="METRIC_FACT",
            statement=f"Invocation volume reached {metric_ev.invocations.deviationRatio:.2f}x the recorded baseline."
        ))

    if err_none:
        summary_facts.append(SummaryFact(
            type="ERROR_FACT",
            statement="No significant Lambda Errors were observed in the collected investigation window."
        ))
    else:
        summary_facts.append(SummaryFact(
            type="ERROR_FACT",
            statement="Lambda Errors were observed during the investigation window."
        ))

    if not thr_present:
        summary_facts.append(SummaryFact(
            type="THROTTLE_FACT",
            statement="No Lambda Throttles were observed in the collected investigation window."
        ))
    else:
        summary_facts.append(SummaryFact(
            type="THROTTLE_FACT",
            statement=f"Lambda Throttling was observed ({metric_ev.throttles.totalThrottles} throttles)."
        ))
        
    return correlations, summary_facts
