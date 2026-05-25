#!/usr/bin/env python3
"""
Script to check ticket counts for a specific set of user IDs.

Can load user IDs from a JSON file and count tickets within a specific date range.

Usage:
  python3 check_user_tickets.py --user-ids-file user_ids.json
  python3 check_user_tickets.py --user-ids-file user_ids.json --since 2024-01-01 --until 2024-12-31
"""

import sys
import csv
import json
import argparse
from config import load_config, ConfigError
from zendesk_client import ZendeskClient, ZendeskAPIError


def load_user_ids(filepath):
    """Load user IDs from a JSON file.
    
    Args:
        filepath (str): Path to JSON file with user_ids array
        
    Returns:
        list: List of user IDs
        
    Raises:
        Exception: If file not found or invalid JSON
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'user_ids' in data:
                return data['user_ids']
            elif isinstance(data, list):
                return data
            else:
                raise ValueError('JSON must contain "user_ids" array or be an array of IDs')
    except FileNotFoundError:
        raise Exception(f'User IDs file not found: {filepath}')
    except json.JSONDecodeError as e:
        raise Exception(f'Invalid JSON in {filepath}: {e}')


def validate_date(date_str):
    """Validate date format YYYY-MM-DD.
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        str: The validated date string
        
    Raises:
        argparse.ArgumentTypeError: If format is invalid
    """
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid date format: {date_str} (expected YYYY-MM-DD)')


def parse_arguments(args):
    """Parse command-line arguments.
    
    Args:
        args (list): Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Check ticket counts for a set of user IDs'
    )
    
    parser.add_argument(
        '--user-ids-file',
        type=str,
        default='user_ids.json',
        help='JSON file containing user IDs (default: user_ids.json)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='user_ticket_counts_report.csv',
        help='Output CSV filename (default: user_ticket_counts_report.csv)'
    )
    
    parser.add_argument(
        '--since',
        type=validate_date,
        default=None,
        help='Start date for ticket count (YYYY-MM-DD, optional)'
    )
    
    parser.add_argument(
        '--until',
        type=validate_date,
        default=None,
        help='End date for ticket count (YYYY-MM-DD, optional)'
    )
    
    return parser.parse_args(args)





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
        # Load user IDs from file
        print(f"Loading user IDs from {parsed_args.user_ids_file}...")
        user_ids = load_user_ids(parsed_args.user_ids_file)
        print(f"Loaded {len(user_ids)} user IDs")
        
        # Load configuration
        config = load_config()
        
        # Initialize Zendesk client
        client = ZendeskClient(config)
        
        # Format date range info
        date_info = ""
        if parsed_args.since or parsed_args.until:
            since = parsed_args.since or "beginning"
            until = parsed_args.until or "today"
            date_info = f" (from {since} to {until})"
        
        print(f"Checking ticket counts for {len(user_ids)} user IDs{date_info}...")
        print("This may take a while due to API rate limits.\n")
        
        # Results list
        results = []
        errors = []
        
        # Count tickets for each user
        for i, user_id in enumerate(user_ids, 1):
            try:
                # Show progress every 50 users
                if i % 50 == 0:
                    print(f"Progress: {i}/{len(user_ids)}", file=sys.stderr)
                
                count = client.count_user_tickets(
                    user_id, 
                    since_date=parsed_args.since,
                    until_date=parsed_args.until
                )
                results.append({
                    'user_id': user_id,
                    'ticket_count': count
                })
                
                # Print user's count if they have tickets
                if count > 0:
                    print(f"User {user_id}: {count} ticket(s)")
                
            except ZendeskAPIError as e:
                print(f"Error checking user {user_id}: {e}", file=sys.stderr)
                errors.append({
                    'user_id': user_id,
                    'error': str(e)
                })
        
        # Write results to CSV
        with open(parsed_args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'ticket_count'])
            writer.writeheader()
            writer.writerows(results)
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Report: {parsed_args.output}")
        print(f"{'='*60}")
        total_tickets = sum(r['ticket_count'] for r in results)
        users_with_tickets = sum(1 for r in results if r['ticket_count'] > 0)
        print(f"Total users checked: {len(results)}")
        print(f"Users with tickets: {users_with_tickets}")
        print(f"Total tickets from these users: {total_tickets}")
        if date_info:
            print(f"Date range: {parsed_args.since or 'all time'} to {parsed_args.until or 'all time'}")
        print(f"Errors: {len(errors)}")
        
        if errors:
            print(f"\nError details:")
            for error_info in errors:
                print(f"  User {error_info['user_id']}: {error_info['error']}")
        
        return 0
        
    except ConfigError as e:
        print(f'Configuration error: {e}', file=sys.stderr)
        return 1
    except Exception as e:
        print(f'Unexpected error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
