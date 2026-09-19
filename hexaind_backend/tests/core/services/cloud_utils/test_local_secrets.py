import pytest
from unittest.mock import patch, MagicMock
from app.core.services.cloud_utils.local_secrets import LocalSecretManager, LocalEnvironment

@pytest.fixture
def mock_local_env():
    with patch('app.core.services.cloud_utils.local_secrets.LocalEnvironment') as mock_env:
        env = MagicMock()
        # Set up environment variables
        env_vars = {
            'TEST_SECRET': 'test-value',
            'ANOTHER_SECRET': 'another-value',
            'CASE_TEST': 'case-sensitive-value'
        }
        env.model_dump.return_value = env_vars
        mock_env.return_value = env
        yield mock_env

def test_local_secret_manager(mock_local_env):
    # Create manager instance
    manager = LocalSecretManager()
    
    # Verify environment was loaded
    mock_local_env.assert_called_once()
    
    # Test fetching a secret
    secret = manager.get_secret("test_secret")
    assert secret == "test-value"
    
    # Test case-insensitive matching
    secret = manager.get_secret("TEST_SECRET")
    assert secret == "test-value"
    
    # Test fetching another secret
    secret = manager.get_secret("another_secret")
    assert secret == "another-value"
    
    # Test caching
    mock_local_env.return_value.model_dump.assert_called_once()
    
    # Second call should use cache
    secret = manager.get_secret("test_secret")
    mock_local_env.return_value.model_dump.assert_called_once()

def test_local_secret_manager_missing_secret(mock_local_env):
    manager = LocalSecretManager()
    
    # Test missing secret
    secret = manager.get_secret("missing_secret")
    assert secret is None

def test_local_secret_manager_reload(mock_local_env):
    manager = LocalSecretManager()
    
    # Initial fetch
    secret = manager.get_secret("test_secret")
    assert secret == "test-value"
    
    # Update environment variables
    new_env_vars = {
        'TEST_SECRET': 'new-value',
        'ANOTHER_SECRET': 'another-value'
    }
    mock_local_env.return_value.model_dump.return_value = new_env_vars
    
    # Reload secrets
    manager.re_fetch_secrets_of_keys_available()
    
    # Verify new value is fetched
    secret = manager.get_secret("test_secret")
    assert secret == "new-value"