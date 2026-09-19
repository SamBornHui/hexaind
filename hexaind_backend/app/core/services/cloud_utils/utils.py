from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from .secret_factory import SecretManagerFactory, CloudProvider
from .secret_base import SecretManagerBase
class CloudConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    CLOUD_PROVIDER: str = "azure"  # default to azure for backward compatibility

def get_secret_manager() -> SecretManagerBase:
    """Get the configured secret manager based on environment settings"""
    config = CloudConfig()
    provider = CloudProvider(config.CLOUD_PROVIDER.lower())
    return SecretManagerFactory.get_secret_manager(provider) 