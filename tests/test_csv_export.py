import csv
import os
import tempfile
from csv_export import write_tickets


def test_write_tickets_creates_valid_csv():
    """Test that write_tickets creates a valid CSV file with correct structure."""
    tickets = [
        {
            'ticket_id': 1,
            'created_date': '2023-01-15T10:00:00Z',
            'status': 'solved',
            'requester_email': 'user1@example.com',
            'requester_organization': 'Acme Corp',
        },
        {
            'ticket_id': 2,
            'created_date': '2023-02-20T14:30:00Z',
            'status': 'open',
            'requester_email': 'user2@example.com',
            'requester_organization': 'Tech Inc',
        },
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'test_tickets.csv')
        write_tickets(tickets, filepath)
        
        assert os.path.exists(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['ticket_id'] == '1'
        assert rows[0]['requester_email'] == 'user1@example.com'
        assert rows[1]['ticket_id'] == '2'
        assert rows[1]['status'] == 'open'


def test_write_tickets_with_empty_list():
    """Test that write_tickets handles empty ticket list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'empty_tickets.csv')
        write_tickets([], filepath)
        
        assert os.path.exists(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have header row only
        assert len(rows) == 0


def test_write_tickets_csv_has_correct_headers():
    """Test that CSV has the correct header row."""
    tickets = [
        {
            'ticket_id': 100,
            'created_date': '2023-03-10T08:00:00Z',
            'status': 'pending',
            'requester_email': 'test@example.com',
            'requester_organization': 'Test Org',
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'headers_test.csv')
        write_tickets(tickets, filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
        
        expected_headers = ['ticket_id', 'created_date', 'status', 
                           'requester_email', 'requester_organization']
        assert headers == expected_headers
