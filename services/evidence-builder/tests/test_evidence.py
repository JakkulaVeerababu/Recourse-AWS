import pytest
from decimal import Decimal
from src.metrics import build_metric_evidence, analyze_invocations
from src.logs import build_log_evidence
from src.configuration import build_configuration_evidence
from src.correlations import build_correlations_and_summaries
from src.scoring import calculate_signal_score
from src.id_generator import generate_evidence_id
from src.handler import handle
from src.models import MetricEvidence, LogEvidence

def test_analyze_invocations():
    meta = {'baseline': Decimal('25'), 'observed': Decimal('138')}
    points = [{'value': 100}, {'value': 138}]
    fact = analyze_invocations(points, meta)
    assert fact.signal == "SIGNIFICANT_INCREASE"
    assert fact.deviationRatio == Decimal('138') / Decimal('25')

def test_build_log_evidence():
    logs_data = [
        {'message': 'Process started'},
        {'message': 'ERROR: something failed'},
        {'message': 'Task timed out after 3.01 seconds'}
    ]
    patterns, signals = build_log_evidence(logs_data)
    
    signal_names = [s.signal for s in signals]
    assert "EXCEPTIONS_PRESENT" in signal_names
    assert "TIMEOUT_LOG_SIGNAL" in signal_names
    
    # check counts
    timeout_pattern = next(p for p in patterns if p['pattern'] == 'Task timed out')
    assert timeout_pattern['count'] == 1

def test_configuration_evidence():
    config = {
        'memorySize': 128,
        'timeout': 3,
        'reserved_concurrency': 'UNRESERVED'
    }
    facts, signals = build_configuration_evidence(config)
    assert 'LOW_MEMORY_CONFIGURATION' in signals
    assert 'SHORT_TIMEOUT_CONFIGURATION' in signals
    assert 'RESERVED_CONCURRENCY_UNSET' in signals

def test_scoring_and_correlations():
    # Setup some basic evidence
    meta = {'baseline': Decimal('25'), 'observed': Decimal('138')}
    inv, err, thr, dur = build_metric_evidence({
        'Invocations': [{'value': 138}],
        'Errors': [],
        'Throttles': []
    }, meta)
    
    metric_ev = MetricEvidence(invocations=inv, errors=err, throttles=thr, duration=dur)
    
    _, log_signals = build_log_evidence([{'message': 'normal'}])
    log_ev = LogEvidence(patterns=[], signals=[s.__dict__ for s in log_signals])
    
    score, level = calculate_signal_score(metric_ev, log_ev)
    assert score == 40  # SIGNIFICANT_INCREASE
    assert level == "MEDIUM"
    
    corrs, facts = build_correlations_and_summaries(metric_ev, log_ev, {})
    corr_types = [c.type for c in corrs]
    assert "TRAFFIC_INCREASE_WITHOUT_ERROR_SPIKE" in corr_types

def test_id_generator():
    ev_id = generate_evidence_id('INC-123', 'CTX-456')
    ev_id_2 = generate_evidence_id('INC-123', 'CTX-456')
    assert ev_id == ev_id_2
    assert ev_id.startswith('EVD-')

def test_handler(monkeypatch):
    monkeypatch.setattr('src.handler.get_incident_meta', lambda *args: {'baseline': Decimal('25'), 'observed': Decimal('138')})
    monkeypatch.setattr('src.handler.get_context', lambda *args: {
        'metrics': {'Invocations': [{'value': 138}]},
        'logs': [],
        'configuration': {}
    })
    
    saved_packages = []
    monkeypatch.setattr('src.handler.save_evidence', lambda pkg: saved_packages.append(pkg))

    result = handle({"incident_id": "INC-1", "context_id": "CTX-1"}, None)
    assert result['status'] == 'EVIDENCE_READY'
    assert result['evidence_id'].startswith('EVD-')
    assert len(saved_packages) == 1
    
    # Prove completeness logic
    pkg = saved_packages[0]
    # Since logs is empty and config is empty in the mock, it should be MINIMAL
    assert pkg['evidenceCompleteness'] == 'MINIMAL'

    # Now test COMPLETE
    monkeypatch.setattr('src.handler.get_context', lambda *args: {
        'metrics': {'Invocations': [{'value': 138}], 'Errors': [{'value': 10}], 'Throttles': [], 'Duration': [{'value': 1}]},
        'logs': [{'message': 'ERROR!'}],
        'configuration': {'Runtime': 'python3.12'}
    })
    saved_packages.clear()
    handle({"incident_id": "INC-1", "context_id": "CTX-1"}, None)
    assert saved_packages[0]['evidenceCompleteness'] == 'COMPLETE'
    assert saved_packages[0]['signalScore'] > 0
