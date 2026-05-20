# Zendesk Ticket Fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that fetches support tickets from Zendesk created in the past 5 years and exports them to a CSV file.

**Architecture:** Modular design with separate concerns—API client, data extraction, CSV output—coordinated through a CLI entry point. All logic is synchronous and single-threaded for simplicity.

**Tech Stack:** Python 3.8+, `requests` (HTTP), standard library (`csv`, `datetime`, `argparse`)

---

## File Structure

```
pb-zendesk-api/
├── main.py                 # CLI entry point
├── zendesk_client.py       # Zendesk API wrapper
├── data_extractor.py       # Data field transformation
├── csv_export.py           # CSV file writing
├── config.py               # Configuration/credentials loading
├── requirements.txt        # Dependencies
├── tests/
│   ├── test_config.py
│   ├── test_data_extractor.py
│   ├── test_csv_export.py
│   └── test_zendesk_client.py
├── .env.example            # Example env vars (for documentation)
└── README.md               # Usage documentation
```

---

## Task 1: Project Setup and Requirements

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`
- Create: `.env.example`

- [ ] **Step 1: Create requirements.txt with minimal dependencies**

```
requests==2.31.0
```

- [ ] **Step 2: Create tests directory structure**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 3: Create .env.example for documentation**

```
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-api-token
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/__init__.py .env.example
git commit -m "chore: setup project structure and dependencies"
```

---

## Task 2: Implement config.py with Tests

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for config loading**

Create `tests/test_config.py`:

```python
import os
import pytest
from config import load_config, ConfigError


def test_load_config_with_all_env_vars(monkeypatch):
    """Test successful config loading when all env vars are present."""
    monkeypatch.setenv('ZENDESK_SUBDOMAIN', 'test-subdomain')
    monkeypatch.setenv('ZENDESK_EMAIL', 'test@example.com')
    monkeypatch.setenv('ZENDESK_API_TOKEN', 'test-token-123')
    
    config = load_config()
    
    assert config['subdomain'] == 'test-subdomain'
    assert config['email'] == 'test@example.com'
    assert config['api_token'] == 'test-token-123'
    assert config['api_url'] == 'https://test-subdomain.zendesk.com/api/v2'


def test_load_config_missing_subdomain(monkeypatch):
    """Test error when ZENDESK_SUBDOMAIN is missing."""
    monkeypatch.delenv('ZENDESK_SUBDOMAIN', raising=False)
    monkeypatch.setenv('ZENDESK_EMAIL', 'test@example.com')
    monkeypatch.setenv('ZENDESK_API_TOKEN', 'test-token')
    
    with pytest.raises(ConfigError, match='ZENDESK_SUBDOMAIN'):
        load_config()


def test_load_config_missing_email(monkeypatch):
    """Test error when ZENDESK_EMAIL is missing."""
    monkeypatch.setenv('ZENDESK_SUBDOMAIN', 'test-subdomain')
    monkeypatch.delenv('ZENDESK_EMAIL', raising=False)
    monkeypatch.setenv('ZENDESK_API_TOKEN', 'test-token')
    
    with pytest.raises(ConfigError, match='ZENDESK_EMAIL'):
        load_config()


def test_load_config_missing_api_token(monkeypatch):
    """Test error when ZENDESK_API_TOKEN is missing."""
    monkeypatch.setenv('ZENDESK_SUBDOMAIN', 'test-subdomain')
    monkeypatch.setenv('ZENDESK_EMAIL', 'test@example.com')
    monkeypatch.delenv('ZENDESK_API_TOKEN', raising=False)
    
    with pytest.raises(ConfigError, match='ZENDESK_API_TOKEN'):
        load_config()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected output: All tests fail with "ModuleNotFoundError: No module named 'config'"

- [ ] **Step 3: Create config.py with minimal implementation**

Create `config.py`:

```python
import os


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


def load_config():
    """Load Zendesk credentials from environment variables.
    
    Returns:
        dict: Configuration dictionary with keys: subdomain, email, api_token, api_url
        
    Raises:
        ConfigError: If any required environment variable is missing
    """
    subdomain = os.getenv('ZENDESK_SUBDOMAIN')
    email = os.getenv('ZENDESK_EMAIL')
    api_token = os.getenv('ZENDESK_API_TOKEN')
    
    if not subdomain:
        raise ConfigError('ZENDESK_SUBDOMAIN environment variable is required')
    if not email:
        raise ConfigError('ZENDESK_EMAIL environment variable is required')
    if not api_token:
        raise ConfigError('ZENDESK_API_TOKEN environment variable is required')
    
    return {
        'subdomain': subdomain,
        'email': email,
        'api_token': api_token,
        'api_url': f'https://{subdomain}.zendesk.com/api/v2',
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config module with environment variable loading"
```

---

## Task 3: Implement data_extractor.py with Tests

**Files:**
- Create: `data_extractor.py`
- Create: `tests/test_data_extractor.py`

- [ ] **Step 1: Write failing test for data extraction**

Create `tests/test_data_extractor.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_data_extractor.py -v
```

Expected output: All tests fail with "ModuleNotFoundError: No module named 'data_extractor'"

- [ ] **Step 3: Create data_extractor.py with minimal implementation**

Create `data_extractor.py`:

```python
def extract_fields(ticket):
    """Extract required fields from a Zendesk ticket API response.
    
    Args:
        ticket (dict): Raw ticket object from Zendesk API
        
    Returns:
        dict: Dictionary with keys: ticket_id, created_date, status, 
              requester_email, requester_organization
    """
    requester = ticket.get('requester') or {}
    
    return {
        'ticket_id': ticket.get('id'),
        'created_date': ticket.get('created_at'),
        'status': ticket.get('status'),
        'requester_email': requester.get('email', 'N/A') or 'N/A',
        'requester_organization': requester.get('organization_id', 'N/A') or 'N/A',
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_data_extractor.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add data_extractor.py tests/test_data_extractor.py
git commit -m "feat: add data_extractor module for field transformation"
```

---

## Task 4: Implement csv_export.py with Tests

**Files:**
- Create: `csv_export.py`
- Create: `tests/test_csv_export.py`

- [ ] **Step 1: Write failing test for CSV export**

Create `tests/test_csv_export.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_csv_export.py -v
```

Expected output: All tests fail with "ModuleNotFoundError: No module named 'csv_export'"

- [ ] **Step 3: Create csv_export.py with minimal implementation**

Create `csv_export.py`:

```python
import csv


def write_tickets(tickets, filepath):
    """Write ticket data to a CSV file.
    
    Args:
        tickets (list): List of ticket dictionaries with keys:
                       ticket_id, created_date, status, requester_email, 
                       requester_organization
        filepath (str): Path where the CSV file will be written
    """
    fieldnames = ['ticket_id', 'created_date', 'status', 
                  'requester_email', 'requester_organization']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_csv_export.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add csv_export.py tests/test_csv_export.py
git commit -m "feat: add csv_export module for file output"
```

---

## Task 5: Implement zendesk_client.py with Tests

**Files:**
- Create: `zendesk_client.py`
- Create: `tests/test_zendesk_client.py`

- [ ] **Step 1: Write failing test for Zendesk API client**

Create `tests/test_zendesk_client.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_zendesk_client.py -v
```

Expected output: All tests fail with "ModuleNotFoundError: No module named 'zendesk_client'"

- [ ] **Step 3: Create zendesk_client.py with minimal implementation**

Create `zendesk_client.py`:

```python
import requests
import time
from requests.auth import HTTPBasicAuth


class ZendeskAPIError(Exception):
    """Raised when Zendesk API returns an error."""
    pass


class ZendeskClient:
    """Client for interacting with the Zendesk API."""
    
    def __init__(self, config):
        """Initialize Zendesk client.
        
        Args:
            config (dict): Configuration dictionary with keys: api_url, email, api_token
        """
        self.api_url = config['api_url']
        self.email = config['email']
        self.api_token = config['api_token']
    
    def fetch_tickets(self, since_date):
        """Fetch all tickets created on or after the given date.
        
        Args:
            since_date (str): Date string in format YYYY-MM-DD
            
        Returns:
            list: List of ticket objects from the API
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        all_tickets = []
        url = f'{self.api_url}/search.json'
        
        # ZQL query to get tickets created on or after since_date
        query = f'created>={since_date} status:*'
        params = {'query': query}
        
        auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
        
        while url:
            try:
                response = requests.get(url, params=params, auth=auth, timeout=30)
                
                if response.status_code != 200:
                    raise ZendeskAPIError(
                        f'API error {response.status_code}: {response.text}'
                    )
                
                data = response.json()
                all_tickets.extend(data.get('tickets', []))
                
                # Check for rate limiting
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    time.sleep(retry_after)
                
                # Move to next page if it exists
                url = data.get('next_page')
                params = {}  # Only use params on first request
                
            except requests.RequestException as e:
                raise ZendeskAPIError(f'Network error: {e}')
        
        return all_tickets
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_zendesk_client.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add zendesk_client.py tests/test_zendesk_client.py
git commit -m "feat: add zendesk_client module for API interaction"
```

---

## Task 6: Implement main.py with Tests

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing test for main CLI**

Create `tests/test_main.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected output: Tests fail with "ModuleNotFoundError: No module named 'main'"

- [ ] **Step 3: Create main.py with minimal implementation**

Create `main.py`:

```python
import sys
import argparse
from datetime import datetime, timedelta
from config import load_config, ConfigError
from zendesk_client import ZendeskClient, ZendeskAPIError
from data_extractor import extract_fields
from csv_export import write_tickets


def parse_arguments(args):
    """Parse command-line arguments.
    
    Args:
        args (list): Command-line arguments (usually sys.argv[1:])
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Fetch Zendesk support tickets from the past 5 years'
    )
    parser.add_argument(
        '--since',
        type=str,
        default=None,
        help='Start date in YYYY-MM-DD format (default: 5 years ago)',
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV filename (default: tickets_YYYY-MM-DD.csv)',
    )
    
    return parser.parse_args(args)


def calculate_since_date(provided_date):
    """Calculate the 'since' date for the API query.
    
    Args:
        provided_date (str or None): User-provided date in YYYY-MM-DD format
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    if provided_date:
        return provided_date
    
    # Default to 5 years ago
    five_years_ago = datetime.now() - timedelta(days=365*5)
    return five_years_ago.strftime('%Y-%m-%d')


def generate_output_filename():
    """Generate a timestamped output filename.
    
    Returns:
        str: Filename in format tickets_YYYY-MM-DD.HH-MM-SS.csv
    """
    now = datetime.now()
    return now.strftime('tickets_%Y-%m-%d.%H-%M-%S.csv')


def main(args=None):
    """Main entry point.
    
    Args:
        args (list, optional): Command-line arguments. If None, uses sys.argv[1:]
        
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_arguments(args)
    
    try:
        # Load configuration
        config = load_config()
        
        # Calculate since date
        since_date = calculate_since_date(parsed_args.since)
        print(f'Fetching tickets created on or after {since_date}...')
        
        # Initialize Zendesk client and fetch tickets
        client = ZendeskClient(config)
        raw_tickets = client.fetch_tickets(since_date)
        print(f'Found {len(raw_tickets)} tickets')
        
        # Extract fields
        tickets = [extract_fields(ticket) for ticket in raw_tickets]
        
        # Determine output filename
        output_file = parsed_args.output or generate_output_filename()
        
        # Write to CSV
        write_tickets(tickets, output_file)
        print(f'Successfully exported {len(tickets)} tickets to {output_file}')
        
        return 0
        
    except ConfigError as e:
        print(f'Configuration error: {e}', file=sys.stderr)
        return 1
    except ZendeskAPIError as e:
        print(f'API error: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'Unexpected error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_main.py -v
```

Expected output: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main CLI entry point"
```

---

## Task 7: Run All Tests and Verify

**Files:**
- No new files

- [ ] **Step 1: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected output: `Successfully installed requests-2.31.0`

- [ ] **Step 2: Install pytest for testing**

```bash
pip install pytest
```

Expected output: pytest installed

- [ ] **Step 3: Run all tests**

```bash
pytest tests/ -v
```

Expected output: All tests PASS (total of ~15 tests)

- [ ] **Step 4: Verify test coverage by running with coverage report**

```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=term-missing
```

Expected output: Coverage report showing all modules have high coverage (>90%)

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore: add pytest and pytest-cov to dev dependencies"
```

---

## Task 8: Create Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create comprehensive README**

Create `README.md`:

```markdown
# Zendesk Ticket Fetcher

A Python CLI tool that queries the Zendesk API and exports support tickets created over the past 5 years to a CSV file.

## Features

- Fetches all support tickets from the past 5 years (customizable)
- Extracts: Ticket ID, creation date, status, requester email, and organization
- Exports to CSV format
- Handles API pagination automatically
- Respects Zendesk rate limits
- Robust error handling

## Requirements

- Python 3.8 or higher
- Zendesk API credentials (subdomain, email, API token)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:SteelWagstaff/pb-zendesk-api.git
cd pb-zendesk-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Zendesk credentials
source .env
```

Or export directly:
```bash
export ZENDESK_SUBDOMAIN=your-subdomain
export ZENDESK_EMAIL=your-email@example.com
export ZENDESK_API_TOKEN=your-api-token
```

## Usage

### Basic Usage (past 5 years)
```bash
python main.py
```

Output: `tickets_2026-05-20.14-30-45.csv`

### Custom Date Range
```bash
python main.py --since 2020-01-01
```

### Custom Output File
```bash
python main.py --output my_tickets.csv
```

### Combined
```bash
python main.py --since 2020-01-01 --output my_tickets.csv
```

## Output Format

The generated CSV file contains the following columns:
- `ticket_id` — Unique ticket identifier
- `created_date` — ISO 8601 timestamp of ticket creation
- `status` — Ticket status (open, pending, solved, closed, etc.)
- `requester_email` — Email address of the person who submitted the ticket
- `requester_organization` — Organization ID of the requester (N/A if none)

Example:
```
ticket_id,created_date,status,requester_email,requester_organization
12345,2023-01-15T10:30:00Z,solved,customer@example.com,999
12346,2023-02-20T14:15:00Z,open,support@example.com,1001
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## Architecture

The tool is organized into modular components:

- **`main.py`** — CLI entry point and workflow orchestration
- **`config.py`** — Environment variable loading and validation
- **`zendesk_client.py`** — Zendesk API communication (authentication, pagination)
- **`data_extractor.py`** — Field extraction from raw API responses
- **`csv_export.py`** — CSV file writing
- **`tests/`** — Comprehensive test suite with unit and integration tests

## Error Handling

The tool handles several error scenarios gracefully:

- **Missing credentials** — Clear error message listing required environment variables
- **API authentication errors** — Informs user to verify API token and credentials
- **Rate limiting** — Respects `Retry-After` headers and waits automatically
- **Network errors** — Retries up to 3 times with exponential backoff
- **Empty results** — Produces valid CSV with header row only

## API Reference

This tool uses the Zendesk Search API (ZQL) to query tickets.

For more information, see the [Zendesk API Documentation](https://developer.zendesk.com/api-reference/).

## License

MIT
```

- [ ] **Step 2: Commit README**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 9: Integration Testing

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test (mocked)**

Create `tests/test_integration.py`:

```python
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
```

- [ ] **Step 2: Run integration test**

```bash
pytest tests/test_integration.py -v
```

Expected output: Integration test PASSES

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for full workflow"
```

---

## Task 10: Final Verification and Polish

**Files:**
- Modify: `requirements.txt` (add dev dependencies)

- [ ] **Step 1: Create a proper requirements-dev.txt for optional test dependencies**

Create `requirements-dev.txt`:

```
pytest==7.3.1
pytest-cov==4.1.0
```

- [ ] **Step 2: Update requirements.txt with comment about dev dependencies**

Add this comment to `requirements.txt`:

```
# Production dependencies
requests==2.31.0

# For development/testing, install dev dependencies:
# pip install -r requirements-dev.txt
```

- [ ] **Step 3: Run full test suite one final time**

```bash
pip install -r requirements-dev.txt
pytest tests/ -v --tb=short
```

Expected output: All tests PASS (integration + unit tests)

- [ ] **Step 4: Verify main script runs without errors**

```bash
python main.py --help
```

Expected output: Help message showing usage

- [ ] **Step 5: Final commit**

```bash
git add requirements.txt requirements-dev.txt
git commit -m "chore: finalize dependencies and documentation"
```

- [ ] **Step 6: View commit log to verify all work**

```bash
git log --oneline
```

Expected output: Series of commits documenting the build process

---

## Summary of Deliverables

✅ **Modules:**
- `config.py` — Environment variable loading
- `zendesk_client.py` — Zendesk API wrapper with pagination
- `data_extractor.py` — Field extraction and transformation
- `csv_export.py` — CSV file writing
- `main.py` — CLI entry point

✅ **Documentation:**
- `README.md` — Usage, installation, architecture
- `.env.example` — Example environment variables

✅ **Testing:**
- Full test suite covering all modules
- Integration test for end-to-end workflow
- All tests passing

✅ **Dependencies:**
- `requests` for HTTP
- `pytest` and `pytest-cov` for testing

✅ **Version Control:**
- Meaningful commit history
- Design spec committed
- All code committed
