import pytest
from unittest.mock import patch
from xrp_track import trace_transactions

def test_trace_transactions_success():
    # Mock get_transactions to return sample data
    with patch('xrp_track.get_transactions') as mock_get:
        mock_get.return_value = {'transactions': [{'Account': 'source', 'Destination': 'dest', 'Amount': {'value': '1000000'}, 'date': '2023-01-01T00:00:00.000Z'}]}
        transactions = trace_transactions('test_account', None, None, max_depth=1)
        assert len(transactions) == 1
        assert transactions[0]['Destination'] == 'dest'

def test_trace_transactions_max_depth():
    # Edge case: stops at max depth
    with patch('xrp_track.get_transactions') as mock_get:
        mock_get.return_value = {'transactions': [{'Account': 'source', 'Destination': 'dest', 'Amount': {'value': '1000000'}}]}
        transactions = trace_transactions('test_account', None, None, max_depth=0)
        assert len(transactions) == 0  # Should not recurse

def test_trace_transactions_no_transactions():
    # Failure scenario: no transactions returned
    with patch('xrp_track.get_transactions') as mock_get:
        mock_get.return_value = {'transactions': []}
        transactions = trace_transactions('test_account', None, None, max_depth=1)
        assert len(transactions) == 0 