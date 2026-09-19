import pytest
from app.core.services.cloud_utils.secret_base import SecretManagerBase

class TestSecretManager(SecretManagerBase):
    def __init__(self):
        super().__init__()
        self._test_secrets = {}
    
    def _fetch_secret_from_vault(self, secret_name: str):
        return self._test_secrets.get(secret_name)
        
    def re_fetch_secrets_of_keys_available(self):
        pass
        
    def set_test_secret(self, key: str, value: str):
        self._test_secrets[key] = value

def test_secret_manager_caching():
    manager = TestSecretManager()
    manager.set_test_secret("test-key", "test-value")
    
    # First call should fetch from vault
    assert manager.get_secret("test-key") == "test-value"
    
    # Second call should use cache
    manager._test_secrets.clear()  # Clear backend but keep cache
    assert manager.get_secret("test-key") == "test-value" 