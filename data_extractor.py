def extract_fields(ticket):
    """Extract required fields from a Zendesk ticket API response.
    
    Args:
        ticket (dict): Raw ticket object from Zendesk API
        
    Returns:
        dict: Dictionary with keys: ticket_id, created_date, status, 
              requester_email, requester_organization
              
    Note: The search API endpoint does not return requester email or 
    organization name—only IDs. Use /api/v2/tickets/{id} for full details.
    """
    return {
        'ticket_id': ticket.get('id'),
        'created_date': ticket.get('created_at'),
        'status': ticket.get('status'),
        'requester_email': 'N/A',  # Not provided by search endpoint
        'requester_organization': ticket.get('organization_id', 'N/A') or 'N/A',
    }
