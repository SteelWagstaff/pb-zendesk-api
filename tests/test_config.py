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
