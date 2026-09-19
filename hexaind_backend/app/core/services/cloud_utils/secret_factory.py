import logging
from enum import Enum
from typing import Optional

from .azure_secrets import AzureSecretManager
from .gcp_secrets import GCPSecretManager
from .local_secrets import LocalSecretManager
from .secret_base import SecretManagerBase

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"


class SecretManagerFactory:
    _instance: Optional[SecretManagerBase] = None

    @classmethod
    def get_secret_manager(cls, provider: CloudProvider) -> SecretManagerBase:
        logger.info(f"Requested secret manager for provider: {provider.name}")
        if cls._instance is None:
            if provider == CloudProvider.AZURE:
                cls._instance = AzureSecretManager()
            elif provider == CloudProvider.GCP:
                cls._instance = GCPSecretManager()
            elif provider == CloudProvider.LOCAL:
                cls._instance = LocalSecretManager()
            else:
                raise ValueError(f"Unsupported cloud provider: {provider}")
        return cls._instance
