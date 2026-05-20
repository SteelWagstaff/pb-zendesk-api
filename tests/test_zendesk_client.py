import pytest
from unittest.mock import Mock, patch
from zendesk_client import ZendeskClient, ZendeskAPIError


def test_zendesk_client_initialization():
    """Test client initialization with config."""
    config = {
        'api_url': 'https://test.zendesk.com/api/v2',
        'email': 'test@example.com',
        'api_token': 'test-token-123',
    }
    
    client = ZendeskClient(config)
    
    assert client.api_url == 'https://test.zendesk.com/api/v2'
    assert client.email == 'test@example.com'
    assert client.api_token == 'test-token-123'


def test_fetch_tickets_makes_correct_request(monkeypatch):
    """Test that fetch_tickets makes correct API request with ZQL query."""
    config = {
        'api_url': 'https://test.zendesk.com/api/v2',
        'email': 'test@example.com',
        'api_token': 'test-token-123',
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {
        'tickets': [
            {'id': 1, 'created_at': '2023-01-15T10:00:00Z', 'status': 'solved'},
        ],
        'count': 1,
        'next_page': None,
    }
    
    monkeypatch.setattr('zendesk_client.requests.get', Mock(return_value=mock_response))
    
    client = ZendeskClient(config)
    tickets = client.fetch_tickets('2023-01-01')
    
    assert len(tickets) == 1
    assert tickets[0]['id'] == 1


def test_fetch_tickets_handles_api_error(monkeypatch):
    """Test error handling when API returns error response."""
    config = {
        'api_url': 'https://test.zendesk.com/api/v2',
        'email': 'test@example.com',
        'api_token': 'test-token-123',
    }
    
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = 'Unauthorized'
    
    monkeypatch.setattr('zendesk_client.requests.get', Mock(return_value=mock_response))
    
    client = ZendeskClient(config)
    
    with pytest.raises(ZendeskAPIError):
        client.fetch_tickets('2023-01-01')


def test_fetch_tickets_with_pagination(monkeypatch):
    """Test that fetch_tickets handles pagination correctly."""
    config = {
        'api_url': 'https://test.zendesk.com/api/v2',
        'email': 'test@example.com',
        'api_token': 'test-token-123',
    }
    
    # First page
    page1_response = Mock()
    page1_response.status_code = 200
    page1_response.headers = {}
    page1_response.json.return_value = {
        'tickets': [
            {'id': 1, 'created_at': '2023-01-15T10:00:00Z', 'status': 'solved'},
            {'id': 2, 'created_at': '2023-01-20T14:30:00Z', 'status': 'open'},
        ],
        'count': 50,
        'next_page': 'https://test.zendesk.com/api/v2/search?page=2',
    }
    
    # Second page
    page2_response = Mock()
    page2_response.status_code = 200
    page2_response.headers = {}
    page2_response.json.return_value = {
        'tickets': [
            {'id': 3, 'created_at': '2023-02-10T08:00:00Z', 'status': 'pending'},
        ],
        'count': 50,
        'next_page': None,
    }
    
    monkeypatch.setattr('zendesk_client.requests.get', 
                       Mock(side_effect=[page1_response, page2_response]))
    
    client = ZendeskClient(config)
    tickets = client.fetch_tickets('2023-01-01')
    
    assert len(tickets) == 3
    assert tickets[0]['id'] == 1
    assert tickets[2]['id'] == 3
