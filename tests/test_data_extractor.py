from data_extractor import extract_fields


def test_extract_fields_with_complete_data():
    """Test extraction of all required fields from a complete ticket."""
    ticket = {
        'id': 12345,
        'created_at': '2023-05-15T10:30:00Z',
        'status': 'solved',
        'requester': {
            'email': 'customer@example.com',
            'organization_id': 999,
            'name': 'John Doe',
        },
    }
    
    result = extract_fields(ticket)
    
    assert result == {
        'ticket_id': 12345,
        'created_date': '2023-05-15T10:30:00Z',
        'status': 'solved',
        'requester_email': 'customer@example.com',
        'requester_organization': 999,
    }


def test_extract_fields_with_missing_requester_email():
    """Test extraction when requester email is missing."""
    ticket = {
        'id': 12346,
        'created_at': '2023-06-20T14:15:00Z',
        'status': 'open',
        'requester': {
            'name': 'Jane Doe',
            'organization_id': 888,
        },
    }
    
    result = extract_fields(ticket)
    
    assert result['requester_email'] == 'N/A'
    assert result['requester_organization'] == 888


def test_extract_fields_with_missing_organization():
    """Test extraction when organization is missing."""
    ticket = {
        'id': 12347,
        'created_at': '2023-07-10T09:00:00Z',
        'status': 'pending',
        'requester': {
            'email': 'user@example.com',
            'name': 'Bob Smith',
        },
    }
    
    result = extract_fields(ticket)
    
    assert result['requester_email'] == 'user@example.com'
    assert result['requester_organization'] == 'N/A'


def test_extract_fields_with_null_requester():
    """Test extraction when requester is null."""
    ticket = {
        'id': 12348,
        'created_at': '2023-08-05T16:45:00Z',
        'status': 'closed',
        'requester': None,
    }
    
    result = extract_fields(ticket)
    
    assert result['requester_email'] == 'N/A'
    assert result['requester_organization'] == 'N/A'
