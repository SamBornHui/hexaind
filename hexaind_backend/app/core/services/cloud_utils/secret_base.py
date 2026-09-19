from abc import ABC, abstractmethod
from typing import Optional, Dict
from threading import Lock
import logging

logger = logging.getLogger(__package__)

class SecretManagerBase(ABC):
    """Abstract base class for cloud secret management"""
    
    def __init__(self):
        self._secrets_dict: Dict[str, str] = {}
        self._lock = Lock()
        
    @abstractmethod
    def _fetch_secret_from_vault(self, secret_name: str) -> Optional[str]:
        """Fetch a single secret from the vault"""
        pass
        
    @abstractmethod
    def re_fetch_secrets_of_keys_available(self) -> None:
        """Refresh all cached secrets"""
        pass
        
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Get secret value, fetching from vault if not cached"""
        with self._lock:
            if secret_name not in self._secrets_dict:
                logger.info(f"Request to get Key:{secret_name}")
                try:
                    secret_value = self._fetch_secret_from_vault(secret_name)
                    if secret_value:
                        logger.info(f"Got Value for {secret_name}")
                        self._secrets_dict[secret_name] = secret_value
                except Exception:
                    logger.exception(f"Failed to fetch Secret value for {secret_name}")
                    
            return self._secrets_dict.get(secret_name)
            
    def fetch_secret_of_keys(self, secret_names: list[str]) -> None:
        """Fetch multiple secrets at once"""
        if not secret_names:
            return
            
        try:
            with self._lock:
                for secret_name in secret_names:
                    logger.info(f"Request for Key:{secret_name}")
                    try:
                        secret_value = self._fetch_secret_from_vault(secret_name)
                        if secret_value:
                            logger.info(f"Got Value for {secret_name}")
                            self._secrets_dict[secret_name] = secret_value
                    except Exception:
                        logger.exception(f"Failed to fetch Secret for key {secret_name}")
        except Exception:
            logger.exception(f"Failed to fetch secrets for Keys: {secret_names}") 