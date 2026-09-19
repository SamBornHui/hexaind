from typing import Optional, Dict
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from .secret_base import SecretManagerBase
from .environment_base import CloudEnvironmentBase

logger = logging.getLogger(__package__)

class LocalEnvironment(CloudEnvironmentBase):
    """Settings class to load environment variables"""
    model_config = SettingsConfigDict(
        env_file=('local.env', '.env'),
        env_file_encoding='utf-8',
        extra='allow',  # Allow any extra fields
        case_sensitive=False  # Make keys case-insensitive
    )

class LocalSecretManager(SecretManagerBase):
    """
    A local secret manager that reads secrets from local.env or .env files.
    This is useful for development and testing purposes.
    """
    
    def __init__(self):
        super().__init__()
        logger.warning(
            "Using LocalSecretManager - This should NEVER be used in production!"
        )
        # Load environment variables
        self.env = LocalEnvironment()
        # Convert environment variables to dictionary
        self._local_secrets = self.env.model_dump()
    
    def _fetch_secret_from_vault(self, secret_name: str) -> Optional[str]:
        """Fetch secret from local environment"""
        # Try exact match first
        if secret_name in self._local_secrets:
            return str(self._local_secrets[secret_name])
            
        # Try case-insensitive match
        secret_name_lower = secret_name.lower()
        for key, value in self._local_secrets.items():
            if key.lower() == secret_name_lower:
                return str(value)
        
        logger.warning(f"Secret {secret_name} not found in local environment")
        return None
    
    def re_fetch_secrets_of_keys_available(self) -> None:
        """Reload secrets from environment files"""
        try:
            # Reload environment
            self.env = LocalEnvironment()
            self._local_secrets = self.env.model_dump()
            
            # Update cached secrets
            with self._lock:
                for secret_name in list(self._secrets_dict.keys()):
                    secret_value = self._fetch_secret_from_vault(secret_name)
                    if secret_value:
                        self._secrets_dict[secret_name] = secret_value
        except Exception:
            logger.exception("Failed to re-fetch secrets from environment")
            raise 