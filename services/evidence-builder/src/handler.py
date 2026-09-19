import json
from datetime import datetime, timezone
from .repository import get_incident_meta, get_context, save_evidence
from .id_generator import generate_evidence_id
from .metrics import build_metric_evidence
from .logs import build_log_evidence
from .configuration import build_configuration_evidence
from .correlations import build_correlations_and_summaries
from .scoring import calculate_signal_score
from .models import MetricEvidence, LogEvidence, EvidencePackage, ConfigurationEvidence

def handle(event, context):
    """
    Step Functions invokes this lambda.
    Input expected:
    {
      "incidentData": { ... },
      "contextResult": {
         "context_id": "CTX-..."
      },
      ...
    }
    Wait, based on the implementation plan, the Step Machine calls `EvidenceBuilder` with:
    {
        "incident_id": "INC-...",
        "context_id": "CTX-..."
    }
    Let's use that cleaner interface.
    """
    incident_id = event.get('incident_id')
    context_id = event.get('context_id')

    if not incident_id or not context_id:
        # Fallback if invoked with entire Step Functions state
        detail = event.get('detail', {})
        incident_id = incident_id or detail.get('incident_id')
        context_result = event.get('contextResult', {})
        context_id = context_id or context_result.get('context_id')

    if not incident_id or not context_id:
        raise ValueError("Missing incident_id or context_id in event")

    # 1. Load Data
    meta = get_incident_meta(incident_id)
    if not meta:
        raise ValueError(f"INCIDENT_NOT_FOUND: {incident_id}")
    
    ctx = get_context(incident_id, context_id)
    if not ctx:
        raise ValueError(f"CONTEXT_NOT_FOUND: {context_id}")

    # 2. Extract Evidence
    # Metrics
    context_metrics = ctx.get('metrics', {})
    inv_fact, err_fact, thr_fact, dur_fact = build_metric_evidence(context_metrics, meta)
    metric_ev = MetricEvidence(
        invocations=inv_fact,
        errors=err_fact,
        throttles=thr_fact,
        duration=dur_fact
    )

    # Configuration
    config_data = ctx.get('configuration', {})
    config_facts, config_signals = build_configuration_evidence(config_data)
    config_ev = ConfigurationEvidence(facts=config_facts, signals=config_signals)

    # Logs
    logs_data = ctx.get('logs', [])
    log_patterns, log_signals_list = build_log_evidence(logs_data)
    log_ev = LogEvidence(
        patterns=log_patterns,
        signals=[s.__dict__ for s in log_signals_list]
    )

    # Correlations & Summaries
    correlations, summary_facts = build_correlations_and_summaries(metric_ev, log_ev, config_ev)

    # Scoring
    score, level = calculate_signal_score(metric_ev, log_ev)

    has_metrics = all(f.status == "COMPLETE" for f in [inv_fact, err_fact, thr_fact, dur_fact])
    has_logs = bool(logs_data)
    has_config = bool(config_data)

    if has_metrics and has_logs and has_config:
        completeness = "COMPLETE"
    elif inv_fact.status == "COMPLETE" and has_config:
        completeness = "PARTIAL"
    else:
        completeness = "MINIMAL"

    # ID
    evidence_id = generate_evidence_id(incident_id, context_id)

    # Build package
    package = EvidencePackage(
        evidenceId=evidence_id,
        incidentId=incident_id,
        contextId=context_id,
        evidenceCompleteness=completeness,
        metricEvidence=metric_ev.to_dict() if hasattr(metric_ev, 'to_dict') else metric_ev.__dict__,
        configurationEvidence=config_ev.__dict__,
        logEvidence=log_ev.__dict__,
        correlations=[c.__dict__ if hasattr(c, '__dict__') else c for c in correlations],
        summaryFacts=[s.__dict__ if hasattr(s, '__dict__') else s for s in summary_facts],
        signalScore=score,
        signalLevel=level,
        generatedAt=datetime.utcnow().isoformat() + "Z",
        resources=[{
            "resourceArn": ctx.get('resource', {}).get('arn', ''),
            "resourceName": ctx.get('resource', {}).get('name', ''),
            "resourceType": ctx.get('resource', {}).get('type', ''),
            "tags": ctx.get('metadata', {}).get('tags', {})
        }]
    )

    # 4. Persist Evidence
    package_dict = package.to_dict()
    # Actually models.py MetricEvidence doesn't inherit dict, we used asdict via EvidencePackage.to_dict()
    
    # Save
    save_evidence(package_dict)

    # Return minimal reference
    return {
        "incident_id": incident_id,
        "context_id": context_id,
        "evidence_id": evidence_id,
        "status": "EVIDENCE_READY"
    }
