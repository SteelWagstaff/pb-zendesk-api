# Zendesk Ticket Fetcher

A Python CLI tool that queries the Zendesk API and exports information about tickets, users, and organizations to CSV files.

## Features

- **Tickets** — Fetch support tickets from any date range (default: all time) with automatic recursive splitting for large date ranges
- **Organizations** — Export all organizations with names, creation dates, and associated domains
- **Users/Requesters** — Export all Zendesk users with metadata
- **User Ticket Counts** — Count tickets opened by specific users or export ticket counts for all users
- Supports user lookup by ID, email, or name
- Exports to CSV format
- Handles API pagination automatically (including cursor-based pagination for unlimited results)
- Respects Zendesk rate limits with automatic delays
- Robust error handling and progress reporting

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

3. Set up environment variables in `.env`:
```bash
cp .env.example .env
# Edit .env with your Zendesk credentials:
# export ZENDESK_SUBDOMAIN=your-zendesk-subdomain
# export ZENDESK_EMAIL=your-email@example.com
# export ZENDESK_API_TOKEN=your-api-token
```

**Note:** The tool automatically loads the `.env` file — no need to manually source it before running commands.

## Usage

### Tickets Command

#### Fetch all time (default)
```bash
python3 main.py tickets
```
Output: `tickets_2026-05-20.14-30-45.csv`

#### Custom date range
```bash
python3 main.py tickets --since 2020-01-01
```

#### Custom output file
```bash
python3 main.py tickets --output my_tickets.csv --since 2020-01-01
```

### Organizations Command

#### Export all organizations
```bash
python3 main.py organizations
```
Output: `organizations.csv` with all organizations (220+)

#### Custom output file
```bash
python3 main.py organizations --output all_orgs.csv
```

### Users Command

#### Export all users/requesters
```bash
python3 main.py users
```
Output: `users.csv` with all users (~25,000)

#### Custom output file
```bash
python3 main.py users --output all_users.csv
```

### User Tickets Command

#### Count tickets by user ID
```bash
python3 main.py user-tickets 123456789012
```
Output: `User 123456789012 has opened 42 ticket(s)`

#### Look up user by email
```bash
python3 main.py user-tickets --email john@example.com
```
Output: `John Doe has opened 42 ticket(s)`

#### Look up user by name
```bash
python3 main.py user-tickets --name "Jane Smith"
```
Output: `Jane Smith has opened 28 ticket(s)`

#### Count tickets in a date range
```bash
python3 main.py user-tickets --email john@example.com --since 2024-01-01 --until 2025-01-01
```
Output: `John Doe has opened 12 ticket(s) between 2024-01-01 and 2025-01-01`

### User Tickets All Command

#### Export all users with ticket counts
```bash
python3 main.py user-tickets-all
```
Output: `user_ticket_counts.csv`

**Note:** This command makes individual API requests for each user and may take a long time for organizations with many end users. It includes automatic rate-limiting (0.1s delay between requests) to prevent API overload.

#### With date range
```bash
python3 main.py user-tickets-all --since 2024-01-01 --until 2025-01-01
```

#### Custom output file
```bash
python3 main.py user-tickets-all --output 2024_user_tickets.csv
```

## Output Format

### Tickets CSV
Columns: `ticket_id, created_date, status, requester_email, requester_organization`

```
ticket_id,created_date,status,requester_email,requester_organization
12345,2023-01-15T10:30:00Z,solved,customer@example.com,361029644271
12346,2023-02-20T14:15:00Z,open,support@example.com,N/A
```

**Note:** `requester_email` is set to "N/A" because the Zendesk search API only returns requester ID, not email. To get actual requester emails, use the `users` command to get the user list and join on user ID.

### Organizations CSV
Columns: `id, name, created_at, updated_at, domain_names`

```
id,name,created_at,updated_at,domain_names
361393733071,Achieving the Dream - OER Course Library,2020-04-10T01:07:59Z,2026-05-02T01:44:19Z,achievingthedream.org
361393733072,Another Org,2020-04-11T02:08:00Z,2026-05-03T02:45:20Z,example1.org; example2.org
```

**Note:** Multiple domain names are separated by semicolons.

### Users CSV
Columns: `id, name, email, created_at, updated_at, organization_id, role`

```
id,name,email,created_at,updated_at,organization_id,role
123456789012,John Doe,john@example.com,2020-04-10T01:07:59Z,2026-05-20T16:21:08Z,999888777666,admin
987654321098,Jane Smith,jane@example.com,2021-06-15T10:30:00Z,2026-05-18T14:45:22Z,999888777666,end-user
```

### User Ticket Counts CSV
Columns: `id, name, email, ticket_count`

```
id,name,email,ticket_count
123456789012,John Doe,john@example.com,42
987654321098,Jane Smith,jane@example.com,28
111222333444,Sam Wilson,sam@example.com,5
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

- **`main.py`** — CLI entry point with subcommands: `tickets`, `organizations`, `users`, `user-tickets`, `user-tickets-all`
- **`config.py`** — Environment variable loading from `.env` file with automatic fallback parsing
- **`zendesk_client.py`** — Zendesk API communication with:
  - `fetch_tickets()` — Recursive date range splitting for large result sets
  - `fetch_organizations()` — Paginated organization retrieval
  - `fetch_users()` — Cursor-based pagination for unlimited user retrieval
  - `count_user_tickets()` — Search-based ticket counting with optional date filters
  - `find_user_by_email()` — User lookup by email
  - `find_user_by_name()` — User search by name
- **`data_extractor.py`** — Field extraction from raw API responses
- **`csv_export.py`** — CSV file writing for tickets, organizations, users, and user ticket counts
- **`tests/`** — Comprehensive test suite with unit and integration tests

## Technical Details

### Pagination Strategy
- **Tickets:** Recursive date range bisection when API response limit is exceeded
- **Organizations:** Standard offset pagination with `next_page` URL following
- **Users:** Cursor-based pagination with `page[size]=100` to avoid offset limits
- **User Tickets:** Search API with optional date filtering

### Rate Limiting
- Automatically respects `Retry-After` headers from API
- `user-tickets-all` command includes 0.1s delay between requests to prevent overwhelming the API
- Expected time: ~40-50 minutes for 24,820 users

## Error Handling

The tool handles several error scenarios gracefully:

- **Missing credentials** — Clear error message listing required environment variables
- **API authentication errors** — Informs user to verify API token and credentials
- **Rate limiting** — Respects `Retry-After` headers and waits automatically
- **Network errors** — Retries with appropriate error messages
- **Empty results** — Produces valid CSV with header row only
- **Large result sets** — Automatically splits date ranges to handle Zendesk's 422 response size limits
- **User lookup not found** — Returns helpful message when email/name lookup fails

## Known Limitations

- **Search API requester details:** The Zendesk search endpoint only returns requester IDs, not emails or organization names. Tickets CSV exports "N/A" for requester email.
- **User ticket count speed:** Counting all users' tickets requires individual API calls per user
- **API rate limits:** Zendesk's free tier may have lower rate limits; enterprise tiers typically allow 200 requests per minute

## API Reference

This tool uses the Zendesk Search API (ZQL) to query tickets.

For more information, see the [Zendesk API Documentation](https://developer.zendesk.com/api-reference/).

## License

MIT
