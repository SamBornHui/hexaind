import pytest
from unittest.mock import patch, MagicMock
from app.core.services.cloud_utils.azure_secrets import AzureSecretManager, AzureEnvironment

@pytest.fixture
def mock_credential():
    with patch('app.core.services.cloud_utils.azure_secrets.ClientSecretCredential') as mock_cred:
        # Create a mock credential instance
        mock_instance = MagicMock()
        mock_cred.return_value = mock_instance
        yield mock_cred

@pytest.fixture
def mock_azure_client(mock_credential):
    with patch('app.core.services.cloud_utils.azure_secrets.SecretClient') as mock_client:
        # Create a mock secret
        mock_secret = MagicMock()
        mock_secret.value = "test-value"
        
        # Create a mock client instance
        mock_instance = MagicMock()
        mock_instance.get_secret.return_value = mock_secret
        
        # Set up the mock client to return our mock instance
        mock_client.return_value = mock_instance
        
        yield mock_client

@pytest.fixture
def mock_azure_env():
    with patch('app.core.services.cloud_utils.azure_secrets.AzureEnvironment') as mock_env:
        env = MagicMock()
        env.azure_tenant_id = "test-tenant"
        env.azure_client_id = "test-client"
        env.azure_client_secret = "test-secret"
        env.azure_key_vault_id = "test-vault"
        mock_env.return_value = env
        yield mock_env

def test_azure_secret_manager(mock_credential, mock_azure_client, mock_azure_env):
    # Create manager instance
    manager = AzureSecretManager()
    
    # Verify credential was created correctly
    mock_credential.assert_called_once_with(
        tenant_id="test-tenant",
        client_id="test-client",
        client_secret="test-secret",
        additionally_allowed_tenants=["*"]
    )
    
    # Verify SecretClient was created correctly
    mock_azure_client.assert_called_once_with(
        vault_url="https://test-vault.vault.azure.net/",
        credential=mock_credential.return_value
    )
    
    # Test fetching a secret
    secret = manager.get_secret("test-secret")
    assert secret == "test-value"
    
    # Test caching
    mock_azure_client.return_value.get_secret.assert_called_once_with("test-secret")
    
    # Second call should use cache
    secret = manager.get_secret("test-secret")
    mock_azure_client.return_value.get_secret.assert_called_once()

def test_azure_secret_manager_error_handling(mock_credential, mock_azure_client, mock_azure_env):
    # Setup client to raise an exception
    mock_azure_client.return_value.get_secret.side_effect = Exception("Test error")
    
    manager = AzureSecretManager()
    
    # Test error handling
    secret = manager.get_secret("test-secret")
    assert secret is None