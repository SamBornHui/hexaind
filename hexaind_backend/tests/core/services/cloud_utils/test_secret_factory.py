import pytest
from unittest.mock import patch
from app.core.services.cloud_utils.secret_factory import SecretManagerFactory, CloudProvider
from app.core.services.cloud_utils.azure_secrets import AzureSecretManager
from app.core.services.cloud_utils.gcp_secrets import GCPSecretManager
from app.core.services.cloud_utils.local_secrets import LocalSecretManager

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton instance before each test"""
    SecretManagerFactory._instance = None
    yield

def test_secret_manager_factory():
    # Test Azure provider
    manager = SecretManagerFactory.get_secret_manager(CloudProvider.AZURE)
    assert isinstance(manager, AzureSecretManager)
    
    # Reset singleton for next test
    SecretManagerFactory._instance = None
    
    # Test GCP provider
    manager = SecretManagerFactory.get_secret_manager(CloudProvider.GCP)
    assert isinstance(manager, GCPSecretManager)
    
    # Reset singleton for next test
    SecretManagerFactory._instance = None
    
    # Test Local provider
    manager = SecretManagerFactory.get_secret_manager(CloudProvider.LOCAL)
    assert isinstance(manager, LocalSecretManager)
    
    # Test singleton pattern
    SecretManagerFactory._instance = None  # Reset first
    manager1 = SecretManagerFactory.get_secret_manager(CloudProvider.AZURE)
    manager2 = SecretManagerFactory.get_secret_manager(CloudProvider.AZURE)
    assert manager1 is manager2  # Should be same instance