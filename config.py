"""
Configuration module for API keys and application settings.
Loads environment variables from .env file.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.

    Args:
        env_path: Optional path to .env file. If not provided, looks in current directory.
    """
    if env_path is None:
        env_path = Path(__file__).parent / '.env'
    else:
        env_path = Path(env_path)

    if not env_path.exists():
        print(f"WARNING: .env file not found at {env_path}")
        return

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable if not already set
                if key not in os.environ:
                    os.environ[key] = value


# Load .env file on import
load_env_file()


class UnsplashConfig:
    """Configuration for Unsplash API."""

    @staticmethod
    def get_application_id() -> str:
        """Get Unsplash Application ID."""
        return os.getenv('UNSPLASH_APPLICATION_ID', '')

    @staticmethod
    def get_access_key() -> str:
        """Get Unsplash Access Key."""
        return os.getenv('UNSPLASH_ACCESS_KEY', '')

    @staticmethod
    def get_secret_key() -> str:
        """Get Unsplash Secret Key."""
        return os.getenv('UNSPLASH_SECRET_KEY', '')

    @staticmethod
    def is_configured() -> bool:
        """Check if Unsplash API is properly configured."""
        return bool(
            UnsplashConfig.get_access_key() and
            UnsplashConfig.get_secret_key()
        )


class AnthropicConfig:
    """
    Configuration for Anthropic Claude API.
    
    DEPRECATED: This application now uses OpenAI GPT-4 Turbo.
    This class is kept for backward compatibility only.
    """

    @staticmethod
    def get_api_key() -> str:
        """Get Anthropic API key (deprecated - use OpenAIConfig instead)."""
        return os.getenv('ANTHROPIC_API_KEY', '')

    @staticmethod
    def is_configured() -> bool:
        """Check if Anthropic API is properly configured (deprecated - use OpenAIConfig instead)."""
        return bool(AnthropicConfig.get_api_key())


class OpenAIConfig:
    """Configuration for OpenAI API."""

    @staticmethod
    def get_api_key() -> str:
        """Get OpenAI API key."""
        return os.getenv('OPENAI_API_KEY', '')

    @staticmethod
    def get_model() -> str:
        """Get OpenAI model to use."""
        return os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')

    @staticmethod
    def is_configured() -> bool:
        """Check if OpenAI API is properly configured."""
        return bool(OpenAIConfig.get_api_key())


# Convenience functions
def get_unsplash_access_key() -> str:
    """Get Unsplash Access Key."""
    return UnsplashConfig.get_access_key()


def get_unsplash_secret_key() -> str:
    """Get Unsplash Secret Key."""
    return UnsplashConfig.get_secret_key()


def get_anthropic_api_key() -> str:
    """Get Anthropic API key."""
    return AnthropicConfig.get_api_key()


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return OpenAIConfig.get_api_key()


class AvionteConfig:
    """Configuration for Avionté API."""

    @staticmethod
    def get_client_id() -> str:
        """Get Avionté OAuth client ID."""
        return os.getenv('AVIONTE_CLIENT_ID', '')

    @staticmethod
    def get_client_secret() -> str:
        """Get Avionté OAuth client secret."""
        return os.getenv('AVIONTE_CLIENT_SECRET', '')

    @staticmethod
    def get_base_url() -> str:
        """Get Avionté API base URL."""
        return os.getenv('AVIONTE_API_BASE_URL', 'https://api.avionte.com')

    @staticmethod
    def get_tenant_id() -> str:
        """Get Avionté tenant/account identifier."""
        return os.getenv('AVIONTE_TENANT_ID', '')

    @staticmethod
    def is_sync_enabled() -> bool:
        """Check if Avionté sync is enabled."""
        return os.getenv('AVIONTE_SYNC_ENABLED', 'false').lower() == 'true'

    @staticmethod
    def get_sync_interval() -> int:
        """Get background sync interval in minutes."""
        return int(os.getenv('AVIONTE_SYNC_INTERVAL', '60'))

    @staticmethod
    def is_configured() -> bool:
        """Check if Avionté API is properly configured."""
        return bool(
            AvionteConfig.get_client_id() and
            AvionteConfig.get_client_secret()
        )


# Convenience function
def get_avionte_client_id() -> str:
    """Get Avionté OAuth client ID."""
    return AvionteConfig.get_client_id()


def get_avionte_client_secret() -> str:
    """Get Avionté OAuth client secret."""
    return AvionteConfig.get_client_secret()


if __name__ == '__main__':
    # Test configuration
    print("Configuration Status:")
    print(f"Unsplash configured: {UnsplashConfig.is_configured()}")
    print(f"OpenAI configured: {OpenAIConfig.is_configured()}")
    print(f"Anthropic configured: {AnthropicConfig.is_configured()} (DEPRECATED)")
    if UnsplashConfig.is_configured():
        print(f"Unsplash Application ID: {UnsplashConfig.get_application_id()}")
        print(f"Unsplash Access Key: {UnsplashConfig.get_access_key()[:20]}...")
    
    if OpenAIConfig.is_configured():
        print(f"OpenAI Model: {OpenAIConfig.get_model()}")
    print(f"Avionté configured: {AvionteConfig.is_configured()}")
    if AvionteConfig.is_configured():
        print(f"Avionté Base URL: {AvionteConfig.get_base_url()}")
        print(f"Avionté Sync Enabled: {AvionteConfig.is_sync_enabled()}")