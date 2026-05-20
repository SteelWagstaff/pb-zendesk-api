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


def write_organizations(organizations, filepath):
    """Write organization data to a CSV file.
    
    Args:
        organizations (list): List of organization dictionaries from Zendesk API
        filepath (str): Path where the CSV file will be written
    """
    fieldnames = ['id', 'name', 'created_at', 'updated_at', 'domain_names']
    
    # Convert domain_names array to comma-separated string
    for org in organizations:
        if 'domain_names' in org and org['domain_names']:
            org['domain_names'] = '; '.join(org['domain_names'])
        else:
            org['domain_names'] = 'N/A'
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='N/A', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(organizations)


def write_users(users, filepath):
    """Write user data to a CSV file.
    
    Args:
        users (list): List of user dictionaries from Zendesk API
        filepath (str): Path where the CSV file will be written
    """
    fieldnames = ['id', 'name', 'email', 'created_at', 'updated_at', 'organization_id', 'role']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='N/A', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(users)


def write_user_ticket_counts(user_counts, filepath):
    """Write user ticket counts to a CSV file.
    
    Args:
        user_counts (list): List of dicts with keys: id, name, email, ticket_count
        filepath (str): Path where the CSV file will be written
    """
    fieldnames = ['id', 'name', 'email', 'ticket_count']
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, restval='N/A', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(user_counts)
