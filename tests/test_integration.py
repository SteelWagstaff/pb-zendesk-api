import tempfile
import os
import csv
from unittest.mock import Mock, patch
from main import main


def test_integration_full_workflow(monkeypatch):
    """Integration test: end-to-end workflow from CLI to CSV output."""
    
    # Mock config
    mock_config = {
        'subdomain': 'test',
        'email': 'test@example.com',
        'api_token': 'token',
        'api_url': 'https://test.zendesk.com/api/v2',
    }
    monkeypatch.setenv('ZENDESK_SUBDOMAIN', 'test')
    monkeypatch.setenv('ZENDESK_EMAIL', 'test@example.com')
    monkeypatch.setenv('ZENDESK_API_TOKEN', 'token')
    
    # Mock API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {
        'tickets': [
            {
                'id': 1,
                'created_at': '2023-01-15T10:00:00Z',
                'status': 'solved',
                'requester': {
                    'email': 'user1@example.com',
                    'organization_id': 'Org1',
                }
            },
            {
                'id': 2,
                'created_at': '2023-02-20T14:30:00Z',
                'status': 'open',
                'requester': {
                    'email': 'user2@example.com',
                    'organization_id': 'Org2',
                }
            },
        ],
        'count': 2,
        'next_page': None,
    }
    
    monkeypatch.setattr('zendesk_client.requests.get', Mock(return_value=mock_response))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'integration_test.csv')
        exit_code = main(['--since', '2023-01-01', '--output', output_file])
        
        assert exit_code == 0
        assert os.path.exists(output_file)
        
        # Verify CSV content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['ticket_id'] == '1'
        assert rows[0]['status'] == 'solved'
        assert rows[1]['requester_email'] == 'user2@example.com'
