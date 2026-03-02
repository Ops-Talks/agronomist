"""Custom exceptions for agronomist."""

from __future__ import annotations


class AgronomistError(Exception):
    """Base exception for all agronomist errors."""


class NetworkError(AgronomistError):
    """Raised when a network/HTTP request fails after retries."""


class AuthenticationError(AgronomistError):
    """Raised when an API token is invalid or lacks permissions."""


class ResolverError(AgronomistError):
    """Raised when a version resolver cannot determine the latest ref."""


class ConfigError(AgronomistError):
    """Raised when agronomist configuration is missing or malformed."""
