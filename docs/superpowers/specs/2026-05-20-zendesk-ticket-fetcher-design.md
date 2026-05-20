# Zendesk Ticket Fetcher - Design Specification
Date: 2026-05-20

## Overview
A Python CLI tool that queries the Zendesk API to fetch support tickets created over the past 5 years and exports the results to a CSV file.

## Requirements
- **Query scope:** Support tickets created in the past 5 years
- **Data to extract:** Ticket ID, creation date, status, requester email, requester organization
- **Output format:** CSV file (timestamped)
- **Interface:** Command-line script with optional date range override
- **Tech stack:** Python with minimal dependencies (`requests` only)

## Architecture

### Module Breakdown
- **`main.py`** — CLI entry point
  - Parses command-line arguments (optional `--since YYYY-MM-DD` flag)
  - Defaults to 5 years ago if no flag provided
  - Orchestrates the workflow: fetch → extract → export
  - Prints success message with output file path

- **`zendesk_client.py`** — Zendesk API wrapper
  - Authenticates with API (email + API token from config)
  - Implements `fetch_tickets(since_date)` that returns paginated results
  - Handles pagination automatically
  - Uses ZQL (Zendesk Query Language) to filter: `created>=YYYY-MM-DD`

- **`data_extractor.py`** — Data transformation
  - Implements `extract_fields(raw_ticket)` that maps API response to: `[id, created_at, status, requester_email, requester_organization]`
  - Handles missing requester info gracefully (fills with "N/A" if not available)

- **`csv_export.py`** — CSV output
  - Implements `write_tickets(tickets, filepath)` that writes list to CSV
  - Uses standard library `csv` module
  - Header row: `ticket_id, created_date, status, requester_email, requester_organization`

- **`config.py`** — Configuration management
  - Loads API credentials from environment variables: `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, `ZENDESK_API_TOKEN`
  - Returns organized dict of config values

- **`requirements.txt`** — Dependencies
  - `requests` (HTTP library)

### Data Flow
1. User runs `python main.py [--since YYYY-MM-DD]`
2. `main.py` loads config and calculates `since_date` (5 years ago by default)
3. `zendesk_client.fetch_tickets(since_date)` queries the API with pagination
4. For each ticket, `data_extractor.extract_fields()` transforms and collects data
5. `csv_export.write_tickets()` writes to timestamped file (e.g., `tickets_2026-05-20.csv`)
6. Success message printed: `"Exported X tickets to tickets_2026-05-20.csv"`

## Error Handling
- **Missing/invalid credentials:** Clear error message, exit with code 1
- **API rate limits:** Respect Zendesk's `Retry-After` header, log and wait
- **Network errors:** Retry up to 3 times with exponential backoff (1s, 2s, 4s), then fail with descriptive message
- **Empty results:** Produce valid CSV with header row only, log info message
- **API errors (4xx, 5xx):** Log full error response, exit with code 1

## File Output
- Filename format: `tickets_YYYY-MM-DD.hh-mm-ss.csv` (timestamp to avoid collisions)
- Location: Current working directory (or configurable)
- CSV encoding: UTF-8

## Testing Strategy
- Unit tests for `data_extractor.extract_fields()` with mock ticket data
- Unit tests for `csv_export.write_tickets()` with file validation
- Integration test for full workflow (will need to mock API responses)

## Success Criteria
- ✅ Tool successfully authenticates to Zendesk API
- ✅ Fetches all tickets from the past 5 years
- ✅ Exports complete, valid CSV with all required fields
- ✅ Handles edge cases (missing data, API errors, rate limits)
- ✅ Clear CLI feedback and error messages
