import sys
import argparse
import time
from datetime import datetime, timedelta
from config import load_config, ConfigError
from zendesk_client import ZendeskClient, ZendeskAPIError
from data_extractor import extract_fields
from csv_export import write_tickets, write_organizations, write_users, write_user_ticket_counts

# Load environment variables from .env file automatically
load_config()


def parse_arguments(args):
    """Parse command-line arguments.
    
    Args:
        args (list): Command-line arguments (usually sys.argv[1:])
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Fetch Zendesk support data'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Tickets command
    tickets_parser = subparsers.add_parser('tickets', help='Fetch support tickets')
    tickets_parser.add_argument(
        '--since',
        type=str,
        default=None,
        help='Start date in YYYY-MM-DD format (default: all time)',
    )
    tickets_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV filename (default: tickets_YYYY-MM-DD.HH-MM-SS.csv)',
    )
    
    # Organizations command
    orgs_parser = subparsers.add_parser('organizations', help='Fetch all organizations')
    orgs_parser.add_argument(
        '--output',
        type=str,
        default='organizations.csv',
        help='Output CSV filename (default: organizations.csv)',
    )
    
    # Users command
    users_parser = subparsers.add_parser('users', help='Fetch all users/requesters')
    users_parser.add_argument(
        '--output',
        type=str,
        default='users.csv',
        help='Output CSV filename (default: users.csv)',
    )
    
    # User tickets command
    user_tickets_parser = subparsers.add_parser(
        'user-tickets',
        help='Count tickets opened by a specific user'
    )
    user_tickets_group = user_tickets_parser.add_mutually_exclusive_group()
    user_tickets_group.add_argument(
        'user_id',
        nargs='?',
        type=str,
        help='User ID to look up',
    )
    user_tickets_group.add_argument(
        '--email',
        type=str,
        help='Look up user by email address',
    )
    user_tickets_group.add_argument(
        '--name',
        type=str,
        help='Search for user by name',
    )
    user_tickets_parser.add_argument(
        '--since',
        type=str,
        help='Start date in YYYY-MM-DD format (optional)',
    )
    user_tickets_parser.add_argument(
        '--until',
        type=str,
        help='End date in YYYY-MM-DD format (optional)',
    )
    
    # User tickets all command
    user_tickets_all_parser = subparsers.add_parser(
        'user-tickets-all',
        help='Export all users with ticket counts to CSV'
    )
    user_tickets_all_parser.add_argument(
        '--output',
        type=str,
        default='user_ticket_counts.csv',
        help='Output CSV filename (default: user_ticket_counts.csv)',
    )
    user_tickets_all_parser.add_argument(
        '--since',
        type=str,
        help='Start date in YYYY-MM-DD format (optional)',
    )
    user_tickets_all_parser.add_argument(
        '--until',
        type=str,
        help='End date in YYYY-MM-DD format (optional)',
    )
    
    parsed = parser.parse_args(args)
    
    # Default to 'tickets' if no command specified
    if not parsed.command:
        parsed.command = 'tickets'
    
    return parsed


def calculate_since_date(provided_date):
    """Calculate the 'since' date for the API query.
    
    Args:
        provided_date (str or None): User-provided date in YYYY-MM-DD format
        
    Returns:
        str or None: Date string in YYYY-MM-DD format, or None for all time
    """
    if provided_date:
        return provided_date
    
    # Default to all time (None means no date constraint)
    return None


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
        
        # Initialize Zendesk client
        client = ZendeskClient(config)
        
        if parsed_args.command == 'tickets':
            # Calculate since date
            since_date = calculate_since_date(parsed_args.since)
            print(f'Fetching tickets created on or after {since_date}...')
            
            # Fetch tickets
            raw_tickets = client.fetch_tickets(since_date)
            print(f'Found {len(raw_tickets)} tickets')
            
            # Extract fields
            tickets = [extract_fields(ticket) for ticket in raw_tickets]
            
            # Determine output filename
            output_file = parsed_args.output or generate_output_filename()
            
            # Write to CSV
            write_tickets(tickets, output_file)
            print(f'Successfully exported {len(tickets)} tickets to {output_file}')
            
        elif parsed_args.command == 'organizations':
            print('Fetching all organizations...')
            
            # Fetch organizations
            organizations = client.fetch_organizations()
            print(f'Found {len(organizations)} organizations')
            
            # Write to CSV
            write_organizations(organizations, parsed_args.output)
            print(f'Successfully exported {len(organizations)} organizations to {parsed_args.output}')
            
        elif parsed_args.command == 'users':
            print('Fetching all users...')
            
            # Fetch users
            users = client.fetch_users()
            print(f'Found {len(users)} users')
            
            # Write to CSV
            write_users(users, parsed_args.output)
            print(f'Successfully exported {len(users)} users to {parsed_args.output}')
        
        elif parsed_args.command == 'user-tickets':
            # Resolve user ID from various lookup methods
            user_id = None
            user_name = None
            
            if parsed_args.user_id:
                user_id = parsed_args.user_id
            elif parsed_args.email:
                user = client.find_user_by_email(parsed_args.email)
                if user:
                    user_id = user['id']
                    user_name = user['name']
                else:
                    print(f"User not found with email: {parsed_args.email}", file=sys.stderr)
                    return 1
            elif parsed_args.name:
                users = client.find_user_by_name(parsed_args.name)
                if not users:
                    print(f"No users found matching: {parsed_args.name}", file=sys.stderr)
                    return 1
                if len(users) > 1:
                    print(f"Multiple users found matching '{parsed_args.name}':")
                    for user in users:
                        print(f"  {user['id']}: {user['name']} ({user.get('email', 'no email')})")
                    return 1
                user_id = users[0]['id']
                user_name = users[0]['name']
            else:
                print("Please provide user ID, --email, or --name", file=sys.stderr)
                return 1
            
            # Count tickets for the user
            count = client.count_user_tickets(user_id, parsed_args.since, parsed_args.until)
            
            # Format output with date range if provided
            date_info = ""
            if parsed_args.since or parsed_args.until:
                since = parsed_args.since or "beginning"
                until = parsed_args.until or "now"
                date_info = f" between {since} and {until}"
            
            display_name = user_name if user_name else f"ID {user_id}"
            print(f'{display_name} has opened {count} ticket(s){date_info}')
        
        elif parsed_args.command == 'user-tickets-all':
            print('Fetching all users and counting their tickets...')
            
            # Fetch all users
            users = client.fetch_users()
            print(f'Found {len(users)} users. Counting tickets...')
            print('Note: This may take a while due to API rate limits. Adding 0.1s delay between requests.')
            
            # Count tickets for each user
            user_counts = []
            for i, user in enumerate(users, 1):
                if i % 100 == 0:
                    print(f'  Progress: {i}/{len(users)}', file=sys.stderr)
                
                try:
                    count = client.count_user_tickets(user['id'], parsed_args.since, parsed_args.until)
                    user_counts.append({
                        'id': user['id'],
                        'name': user.get('name', 'N/A'),
                        'email': user.get('email', 'N/A'),
                        'ticket_count': count
                    })
                except ZendeskAPIError as e:
                    print(f"Warning: Failed to count tickets for user {user['id']}: {e}", file=sys.stderr)
                    user_counts.append({
                        'id': user['id'],
                        'name': user.get('name', 'N/A'),
                        'email': user.get('email', 'N/A'),
                        'ticket_count': 'ERROR'
                    })
                
                # Add delay to respect rate limits
                time.sleep(0.1)
            
            # Write to CSV
            write_user_ticket_counts(user_counts, parsed_args.output)
            print(f'Successfully exported {len(user_counts)} users with ticket counts to {parsed_args.output}')
        
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
