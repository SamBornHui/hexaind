from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import logging

logger = logging.getLogger(__package__)

class CloudEnvironmentBase(BaseSettings):
    """Base class for cloud environment settings"""
    model_config = SettingsConfigDict(
        env_file=('.env'),
        env_file_encoding='utf-8',
        extra="ignore",
    )
    
    # Common field across all cloud providers
    vault_secret_names_sep_by_comma: str = ""
    
    def get_vault_secret_names_list(self) -> List[str]:
        """Get list of secret names from comma-separated string"""
        secret_names_list = []
        try:
            if self.vault_secret_names_sep_by_comma and len(self.vault_secret_names_sep_by_comma) > 0:
                vault_secret_names_csv = self.vault_secret_names_sep_by_comma.replace(' ', '')
                secret_names_list = vault_secret_names_csv.split(',')
        except Exception:
            logger.exception("Exception while trying to split secret names to list")
        return secret_names_list 