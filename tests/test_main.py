import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from main import parse_arguments, calculate_since_date, main


def test_parse_arguments_no_args():
    """Test argument parsing with no arguments."""
    args = parse_arguments([])
    
    assert args.since is None
    assert args.output is None


def test_parse_arguments_with_since():
    """Test argument parsing with --since flag."""
    args = parse_arguments(['--since', '2020-01-01'])
    
    assert args.since == '2020-01-01'


def test_parse_arguments_with_output():
    """Test argument parsing with --output flag."""
    args = parse_arguments(['--output', 'my_tickets.csv'])
    
    assert args.output == 'my_tickets.csv'


def test_calculate_since_date_default():
    """Test default since_date calculation (5 years ago)."""
    since = calculate_since_date(None)
    
    # Should be approximately 5 years ago
    expected = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
    # Allow for slight date variation due to leap years
    assert since[:4] == expected[:4]  # Same year
    assert since[5:7] == expected[5:7]  # Same month


def test_calculate_since_date_with_provided_date():
    """Test since_date when explicitly provided."""
    since = calculate_since_date('2020-06-15')
    
    assert since == '2020-06-15'


def test_main_full_workflow(monkeypatch):
    """Test full main workflow with mocked components."""
    # Mock config loading
    mock_config = {
        'subdomain': 'test',
        'email': 'test@example.com',
        'api_token': 'token',
        'api_url': 'https://test.zendesk.com/api/v2',
    }
    monkeypatch.setattr('main.load_config', Mock(return_value=mock_config))
    
    # Mock Zendesk client
    mock_tickets = [
        {
            'id': 1,
            'created_at': '2023-01-15T10:00:00Z',
            'status': 'solved',
            'requester': {'email': 'user@example.com', 'organization_id': 'Org1'},
        }
    ]
    mock_client = Mock()
    mock_client.fetch_tickets.return_value = mock_tickets
    monkeypatch.setattr('main.ZendeskClient', Mock(return_value=mock_client))
    
    # Mock data extractor
    monkeypatch.setattr('main.extract_fields', Mock(return_value={
        'ticket_id': 1,
        'created_date': '2023-01-15T10:00:00Z',
        'status': 'solved',
        'requester_email': 'user@example.com',
        'requester_organization': 'Org1',
    }))
    
    # Mock CSV export
    monkeypatch.setattr('main.write_tickets', Mock())
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'test_tickets.csv')
        exit_code = main(['--output', output_file])
    
    assert exit_code == 0
