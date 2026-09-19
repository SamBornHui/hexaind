from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging
from .secret_base import SecretManagerBase
from .environment_base import CloudEnvironmentBase

logger = logging.getLogger(__package__)

class AzureEnvironment(CloudEnvironmentBase):
    model_config = SettingsConfigDict(
        env_file=('azure.env', '.env'),
        env_file_encoding='utf-8',
        extra="ignore",
    )
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    azure_key_vault_id: str
    azure_users_sync_in_mins: int = 1

class AzureSecretManager(SecretManagerBase):
    def __init__(self):
        super().__init__()
        self.env = AzureEnvironment()
        self._vault_url = f'https://{self.env.azure_key_vault_id}.vault.azure.net/'
        self._credential = ClientSecretCredential(
            tenant_id=self.env.azure_tenant_id,
            client_id=self.env.azure_client_id,
            client_secret=self.env.azure_client_secret,
            additionally_allowed_tenants=["*"]
        )
        self._client = SecretClient(vault_url=self._vault_url, credential=self._credential)

    def _fetch_secret_from_vault(self, secret_name: str) -> Optional[str]:
        try:
            retrieved_secret = self._client.get_secret(secret_name)
            return retrieved_secret.value if retrieved_secret else None
        except Exception:
            logger.exception(f"Failed to fetch secret {secret_name}")
            return None

    def re_fetch_secrets_of_keys_available(self) -> None:
        try:
            with self._lock:
                for secret_name in self._secrets_dict:
                    secret_value = self._fetch_secret_from_vault(secret_name)
                    if secret_value:
                        self._secrets_dict[secret_name] = secret_value
        except Exception:
            logger.exception("Failed to re-fetch secrets")
            raise 