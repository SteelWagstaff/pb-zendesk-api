import requests
import time
from datetime import datetime, timedelta
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
            since_date (str or None): Date string in format YYYY-MM-DD, or None for all time
            
        Returns:
            list: List of ticket objects from the API
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        return self._fetch_tickets_recursive(since_date, datetime.now().strftime('%Y-%m-%d'))
    
    def _fetch_tickets_recursive(self, since_date, until_date, depth=0):
        """Recursively fetch tickets, splitting date ranges if response is too large.
        
        Args:
            since_date (str): Start date in format YYYY-MM-DD
            until_date (str): End date in format YYYY-MM-DD
            depth (int): Recursion depth for logging
            
        Returns:
            list: List of ticket objects from the API
        """
        all_tickets = []
        url = f'{self.api_url}/search.json'
        
        # Prevent infinite recursion
        if depth > 50:
            print(f'[Depth {depth}] Reached max recursion depth for {since_date} to {until_date}')
            return []
        
        # ZQL query to get tickets in the specified date range
        # If since_date is None, query all time (only constrain until_date)
        if since_date:
            query = f'created>={since_date} created<={until_date}'
        else:
            query = f'created<={until_date}'
        params = {'query': query}
        
        auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
        first_request = True
        
        while url:
            try:
                # Only add params on the first request
                if first_request:
                    params['limit'] = 100
                    response = requests.get(url, params=params, auth=auth, timeout=30)
                    first_request = False
                else:
                    response = requests.get(url, auth=auth, timeout=30)
                
                # Check for response size limit error (422)
                if response.status_code == 422:
                    error_msg = response.text
                    if 'response size' in error_msg.lower():
                        # Response too large - split the date range and retry
                        if since_date is None:
                            # If querying all time, start from a reasonable historical point
                            # Use Zendesk's founding year as a practical default
                            since_date = '2007-01-01'
                        
                        since_dt = datetime.strptime(since_date, '%Y-%m-%d')
                        until_dt = datetime.strptime(until_date, '%Y-%m-%d')
                        mid_dt = since_dt + (until_dt - since_dt) / 2
                        mid_date = mid_dt.strftime('%Y-%m-%d')
                        
                        print(f'Response too large for {since_date} to {until_date}. Splitting...')
                        
                        # Recursively fetch both halves
                        all_tickets.extend(self._fetch_tickets_recursive(since_date, mid_date))
                        # Add one day to avoid duplicates at the boundary
                        next_date = (mid_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                        all_tickets.extend(self._fetch_tickets_recursive(next_date, until_date))
                        return all_tickets
                    else:
                        raise ZendeskAPIError(f'API error {response.status_code}: {response.text}')
                elif response.status_code != 200:
                    raise ZendeskAPIError(
                        f'API error {response.status_code}: {response.text}'
                    )
                
                data = response.json()
                all_tickets.extend(data.get('results', []))
                
                # Check for rate limiting
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    time.sleep(retry_after)
                
                # Move to next page if it exists
                url = data.get('next_page')
                
            except requests.RequestException as e:
                raise ZendeskAPIError(f'Network error: {e}')
        
        return all_tickets
    
    def fetch_organizations(self):
        """Fetch all organizations.
        
        Returns:
            list: List of organization objects from the API
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        all_organizations = []
        url = f'{self.api_url}/organizations.json'
        auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
        
        while url:
            try:
                response = requests.get(url, auth=auth, timeout=30)
                
                if response.status_code != 200:
                    raise ZendeskAPIError(
                        f'API error {response.status_code}: {response.text}'
                    )
                
                data = response.json()
                all_organizations.extend(data.get('organizations', []))
                
                # Check for rate limiting
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    time.sleep(retry_after)
                
                # Move to next page if it exists
                url = data.get('next_page')
                
            except requests.RequestException as e:
                raise ZendeskAPIError(f'Network error: {e}')
        
        return all_organizations
    
    def fetch_users(self):
        """Fetch all users/requesters using cursor-based pagination.
        
        Returns:
            list: List of user objects from the API
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        all_users = []
        url = f'{self.api_url}/users.json?page[size]=100'  # Cursor pagination format
        auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
        
        while url:
            try:
                response = requests.get(url, auth=auth, timeout=30)
                
                if response.status_code != 200:
                    raise ZendeskAPIError(
                        f'API error {response.status_code}: {response.text}'
                    )
                
                data = response.json()
                all_users.extend(data.get('users', []))
                
                # Check for rate limiting
                if 'Retry-After' in response.headers:
                    retry_after = int(response.headers['Retry-After'])
                    time.sleep(retry_after)
                
                # Move to next page if it exists (cursor pagination uses links.next)
                links = data.get('links', {})
                url = links.get('next')
                
            except requests.RequestException as e:
                raise ZendeskAPIError(f'Network error: {e}')
        
        return all_users
    
    def count_user_tickets(self, user_id, since_date=None, until_date=None):
        """Count how many tickets a user has opened.
        
        Args:
            user_id (str or int): The Zendesk user ID
            since_date (str, optional): Start date in YYYY-MM-DD format
            until_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            int: Number of tickets opened by the user
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        try:
            query = f'type:ticket requester_id:{user_id}'
            
            # Add date filters if provided
            if since_date:
                query += f' created>={since_date}'
            if until_date:
                query += f' created<{until_date}'
            
            url = f'{self.api_url}/search.json?query={query}'
            auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
            
            response = requests.get(url, auth=auth, timeout=30)
            
            if response.status_code != 200:
                raise ZendeskAPIError(
                    f'API error {response.status_code}: {response.text}'
                )
            
            data = response.json()
            return data.get('count', 0)
            
        except requests.RequestException as e:
            raise ZendeskAPIError(f'Network error: {e}')
    
    def find_user_by_email(self, email):
        """Find a user by email address.
        
        Args:
            email (str): Email address to search for
            
        Returns:
            dict: User object if found, None otherwise
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        try:
            url = f'{self.api_url}/users/search.json?query={email}'
            auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
            
            response = requests.get(url, auth=auth, timeout=30)
            
            if response.status_code != 200:
                raise ZendeskAPIError(
                    f'API error {response.status_code}: {response.text}'
                )
            
            data = response.json()
            users = data.get('users', [])
            
            # Find exact email match
            for user in users:
                if user.get('email', '').lower() == email.lower():
                    return user
            
            # If no exact match, return first result if any
            return users[0] if users else None
            
        except requests.RequestException as e:
            raise ZendeskAPIError(f'Network error: {e}')
    
    def find_user_by_name(self, name):
        """Find a user by name (partial match).
        
        Args:
            name (str): Name or partial name to search for
            
        Returns:
            list: List of matching user objects
            
        Raises:
            ZendeskAPIError: If API request fails
        """
        try:
            url = f'{self.api_url}/users/search.json?query={name}'
            auth = HTTPBasicAuth(f'{self.email}/token', self.api_token)
            
            response = requests.get(url, auth=auth, timeout=30)
            
            if response.status_code != 200:
                raise ZendeskAPIError(
                    f'API error {response.status_code}: {response.text}'
                )
            
            data = response.json()
            return data.get('users', [])
            
        except requests.RequestException as e:
            raise ZendeskAPIError(f'Network error: {e}')
