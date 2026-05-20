import os

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


def load_config():
    """Load environment variables from .env file if dotenv is available."""
    if HAS_DOTENV:
        # Try loading from .env in current directory
        load_dotenv('.env')
        # Also try loading from parent directories
        load_dotenv()
    
    # Also try loading from current directory by reading .env manually
    # This allows .env to work even without python-dotenv installed
    env_file = '.env'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        # Handle export prefix if present
                        if line.startswith('export '):
                            line = line[7:]
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\'"')
                        if key and not os.getenv(key):
                            os.environ[key] = value
        except Exception:
            pass  # Silently fail if .env can't be read
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
