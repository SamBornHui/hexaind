import logging
from typing import Optional

from google.cloud import secretmanager
from google.oauth2 import service_account
from pydantic_settings import BaseSettings, SettingsConfigDict

from .environment_base import CloudEnvironmentBase
from .secret_base import SecretManagerBase

logger = logging.getLogger(__package__)


class GCPEnvironment(CloudEnvironmentBase):
    model_config = SettingsConfigDict(
        env_file=("gcp.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    gcp_project_id: str
    gcp_client_email: str
    gcp_private_key_id: str
    gcp_private_key: str
    gcp_client_id: str


class GCPSecretManager(SecretManagerBase):
    def __init__(self):
        super().__init__()
        self.env = GCPEnvironment()

        # Create credentials from environment variables
        credentials_dict = {
            "type": "service_account",
            "project_id": self.env.gcp_project_id,
            "private_key_id": self.env.gcp_private_key_id,
            "private_key": self.env.gcp_private_key,
            "client_email": self.env.gcp_client_email,
            "client_id": self.env.gcp_client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.env.gcp_client_email}",
        }

        # Create credentials object
        self._credentials = service_account.Credentials.from_service_account_info(
            credentials_dict, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        # Create authenticated client
        self._client = secretmanager.SecretManagerServiceClient(
            credentials=self._credentials
        )
        self._project_path = f"projects/{self.env.gcp_project_id}"

    def _fetch_secret_from_vault(self, secret_name: str) -> Optional[str]:
        try:
            name = f"{self._project_path}/secrets/{secret_name}/versions/latest"
            response = self._client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
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
