"""
Secure Configuration Module
Handles Azure Key Vault secret retrieval using Managed Identity
"""

from typing import Dict, Any, Optional
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from frmk.utils.logging import get_logger

logger = get_logger("secure_config")


class SecureConfig:
    """
    Secure configuration manager using Azure Key Vault

    Features:
    - Uses DefaultAzureCredential (supports Managed Identity, Azure CLI, etc.)
    - Caches secrets in memory
    - Falls back to environment variables if Key Vault unavailable
    - Thread-safe
    """

    def __init__(self, key_vault_url: Optional[str] = None):
        """
        Initialize SecureConfig

        Args:
            key_vault_url: Azure Key Vault URL (e.g., https://mykv.vault.azure.net/)
                          If None, reads from KEY_VAULT_URL environment variable
        """
        self.key_vault_url = key_vault_url or os.getenv("KEY_VAULT_URL")
        self._cache: Dict[str, str] = {}
        self._client: Optional[SecretClient] = None

        if self.key_vault_url:
            try:
                credential = DefaultAzureCredential()
                self._client = SecretClient(
                    vault_url=self.key_vault_url,
                    credential=credential
                )
                logger.info(f"SecureConfig initialized with Key Vault: {self.key_vault_url}")
            except Exception as e:
                logger.warning(f"Failed to initialize Key Vault client: {e}")
                self._client = None
        else:
            logger.info("SecureConfig initialized in environment-only mode (no Key Vault)")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Key Vault or environment variable

        Priority:
        1. Cache (if already fetched)
        2. Azure Key Vault (if configured)
        3. Environment variable (fallback)
        4. Default value (if provided)

        Args:
            secret_name: Secret name (e.g., "COSMOS-CONNECTION-STRING")
            default: Default value if secret not found

        Returns:
            Secret value or None
        """
        # Check cache
        if secret_name in self._cache:
            return self._cache[secret_name]

        # Try Key Vault
        if self._client:
            try:
                secret = self._client.get_secret(secret_name)
                value = secret.value
                self._cache[secret_name] = value
                logger.debug(f"Retrieved secret '{secret_name}' from Key Vault")
                return value
            except Exception as e:
                logger.warning(f"Failed to get secret '{secret_name}' from Key Vault: {e}")

        # Fallback to environment variable
        env_name = secret_name.replace("-", "_").upper()
        value = os.getenv(env_name, default)

        if value:
            self._cache[secret_name] = value
            logger.debug(f"Retrieved secret '{secret_name}' from environment")
        else:
            logger.warning(f"Secret '{secret_name}' not found in Key Vault or environment")

        return value

    def get_connection_string(self, service: str) -> str:
        """
        Get connection string for Azure service

        Args:
            service: Service name (e.g., "cosmos", "redis", "signalr")

        Returns:
            Connection string

        Raises:
            ValueError: If connection string not found
        """
        secret_name = f"{service.upper()}-CONNECTION-STRING"
        value = self.get_secret(secret_name)

        if not value:
            raise ValueError(f"Connection string for {service} not found")

        return value

    def get_api_key(self, service: str) -> str:
        """
        Get API key for external service

        Args:
            service: Service name (e.g., "openai", "flight-api")

        Returns:
            API key

        Raises:
            ValueError: If API key not found
        """
        secret_name = f"{service.upper()}-API-KEY"
        value = self.get_secret(secret_name)

        if not value:
            raise ValueError(f"API key for {service} not found")

        return value

    def get_all_secrets(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Get all secrets (from cache and environment)

        Args:
            prefix: Optional prefix filter

        Returns:
            Dictionary of secret names to values
        """
        secrets = self._cache.copy()

        # Add environment variables
        for key, value in os.environ.items():
            if prefix is None or key.startswith(prefix):
                secrets[key] = value

        return secrets

    def clear_cache(self):
        """Clear the secret cache"""
        self._cache.clear()
        logger.info("Secret cache cleared")


# Global singleton
_secure_config: Optional[SecureConfig] = None


def get_secure_config(key_vault_url: Optional[str] = None) -> SecureConfig:
    """
    Get or create SecureConfig singleton

    Args:
        key_vault_url: Key Vault URL (only used on first call)

    Returns:
        SecureConfig instance
    """
    global _secure_config

    if _secure_config is None:
        _secure_config = SecureConfig(key_vault_url)

    return _secure_config


def reset_secure_config():
    """Reset global secure config (useful for testing)"""
    global _secure_config
    _secure_config = None
