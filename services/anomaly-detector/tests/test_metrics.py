import pytest
from src.metrics import calculate_baseline
from src.config import MIN_BASELINE_PERIODS

def test_calculate_baseline_valid():
    values = [20, 25, 30]
    assert calculate_baseline(values) == 25.0

def test_calculate_baseline_insufficient_data():
    values = [20, 25]
    # MIN_BASELINE_PERIODS is 3
    assert calculate_baseline(values) is None

def test_calculate_baseline_filters_breaches():
    values = [25, 25, 145, 25]
    # The 145 should be filtered out, leaving three 25s
    assert calculate_baseline(values) == 25.0

def test_calculate_baseline_zero_values():
    values = [0, 0, 0]
    assert calculate_baseline(values) == 0.0
