import pytest
from src.severity import calculate_severity

def test_calculate_severity_none():
    assert calculate_severity(None) == "UNKNOWN"

def test_calculate_severity_low():
    assert calculate_severity(1.0) == "LOW"
    assert calculate_severity(1.9) == "LOW"

def test_calculate_severity_medium():
    assert calculate_severity(2.0) == "MEDIUM"
    assert calculate_severity(4.99) == "MEDIUM"

def test_calculate_severity_high():
    assert calculate_severity(5.0) == "HIGH"
    assert calculate_severity(9.99) == "HIGH"

def test_calculate_severity_critical():
    assert calculate_severity(10.0) == "CRITICAL"
    assert calculate_severity(100.0) == "CRITICAL"

def test_calculate_severity_phase_3_proof():
    # Prove: baseline = 25, observed = 140, deviation = 5.6, severity = HIGH
    baseline = 25.0
    observed = 140.0
    deviation = observed / baseline
    assert deviation == 5.6
    assert calculate_severity(deviation) == "HIGH"

