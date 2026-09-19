import pytest
from unittest.mock import patch, MagicMock
from app.core.services.cloud_utils.gcp_secrets import GCPSecretManager, GCPEnvironment

@pytest.fixture
def mock_credential():
    with patch('app.core.services.cloud_utils.gcp_secrets.service_account.Credentials') as mock_cred:
        # Create a mock credential instance
        mock_instance = MagicMock()
        mock_cred.from_service_account_info.return_value = mock_instance
        yield mock_cred

@pytest.fixture
def mock_gcp_client(mock_credential):
    with patch('app.core.services.cloud_utils.gcp_secrets.secretmanager.SecretManagerServiceClient') as mock_client:
        # Create a mock secret
        mock_version = MagicMock()
        mock_version.payload.data.decode.return_value = "test-value"
        
        # Create a mock client instance
        mock_instance = MagicMock()
        mock_instance.access_secret_version.return_value = mock_version
        
        # Set up the mock client to return our mock instance
        mock_client.return_value = mock_instance
        
        yield mock_client

@pytest.fixture
def mock_gcp_env():
    with patch('app.core.services.cloud_utils.gcp_secrets.GCPEnvironment') as mock_env:
        env = MagicMock()
        env.gcp_project_id = "test-project"
        env.gcp_client_email = "test@example.com"
        env.gcp_private_key_id = "test-key-id"
        env.gcp_private_key = "test-key"
        env.gcp_client_id = "test-client"
        mock_env.return_value = env
        yield mock_env

def test_gcp_secret_manager(mock_credential, mock_gcp_client, mock_gcp_env):
    # Create manager instance
    manager = GCPSecretManager()
    
    # Verify credential was created correctly
    mock_credential.from_service_account_info.assert_called_once_with(
        {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "test-key",
            "client_email": "test@example.com",
            "client_id": "test-client",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test@example.com",
        },
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    
    # Verify SecretManagerServiceClient was created correctly
    mock_gcp_client.assert_called_once_with(
        credentials=mock_credential.from_service_account_info.return_value
    )
    
    # Test fetching a secret
    secret = manager.get_secret("test-secret")
    assert secret == "test-value"
    
    # Test caching
    mock_gcp_client.return_value.access_secret_version.assert_called_once_with(
        request={"name": "projects/test-project/secrets/test-secret/versions/latest"}
    )
    
    # Second call should use cache
    secret = manager.get_secret("test-secret")
    mock_gcp_client.return_value.access_secret_version.assert_called_once()

def test_gcp_secret_manager_error_handling(mock_credential, mock_gcp_client, mock_gcp_env):
    # Setup client to raise an exception
    mock_gcp_client.return_value.access_secret_version.side_effect = Exception("Test error")
    
    manager = GCPSecretManager()
    
    # Test error handling
    secret = manager.get_secret("test-secret")
    assert secret is None
 