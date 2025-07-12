import pytest
from xrp_track import detect_heuristics

def test_detect_heuristics_mixer_detection():
    # Success path: detects mixer with >10 incoming txns
    transactions = [{'Destination': 'test_account'}] * 11
    alerts = []
    detect_heuristics(transactions, 'test_account', alerts)
    assert len(alerts) == 1
    assert 'suspected as mixer' in alerts[0]

def test_detect_heuristics_no_mixer():
    # Failure scenario: no detection with <=10 incoming
    transactions = [{'Destination': 'test_account'}] * 10
    alerts = []
    detect_heuristics(transactions, 'test_account', alerts)
    assert len(alerts) == 0

def test_detect_heuristics_edge_case_empty():
    # Edge case: empty transactions
    transactions = []
    alerts = []
    detect_heuristics(transactions, 'test_account', alerts)
    assert len(alerts) == 0 