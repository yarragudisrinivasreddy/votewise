"""Custom exception hierarchy for VoteWise.

Defines domain-specific exceptions with clear semantics,
enabling precise error handling throughout the application.
"""

from __future__ import annotations

__all__ = [
    "VoteWiseError",
    "ConfigurationError",
    "ServiceUnavailableError",
    "TranslationError",
    "GenerationError",
    "ValidationError",
    "StorageError",
]


class VoteWiseError(Exception):
    """Base exception for all VoteWise application errors.

    All application-specific exceptions inherit from this class,
    enabling catch-all handling at the API boundary.
    """

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        """Initialise VoteWiseError.

        Args:
            message: Human-readable description of the error.
            code: Machine-readable error code for API responses.
        """
        super().__init__(message)
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        """Return developer-friendly string representation."""
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class ConfigurationError(VoteWiseError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, key: str) -> None:
        """Initialise ConfigurationError.

        Args:
            key: The missing or invalid configuration key.
        """
        super().__init__(
            message=f"Required configuration key '{key}' is missing or invalid.",
            code="CONFIGURATION_ERROR",
        )
        self.key = key


class ServiceUnavailableError(VoteWiseError):
    """Raised when an external Google Cloud service is unreachable."""

    def __init__(self, service: str, reason: str) -> None:
        """Initialise ServiceUnavailableError.

        Args:
            service: The name of the unavailable service.
            reason: A brief description of why the service is unavailable.
        """
        super().__init__(
            message=f"Service '{service}' is unavailable: {reason}",
            code="SERVICE_UNAVAILABLE",
        )
        self.service = service
        self.reason = reason


class TranslationError(VoteWiseError):
    """Raised when Cloud Translate fails to process a translation request."""

    def __init__(self, source_lang: str, target_lang: str, reason: str) -> None:
        """Initialise TranslationError.

        Args:
            source_lang: BCP-47 source language code.
            target_lang: BCP-47 target language code.
            reason: Reason the translation failed.
        """
        super().__init__(
            message=f"Translation from '{source_lang}' to '{target_lang}' failed: {reason}",
            code="TRANSLATION_ERROR",
        )
        self.source_lang = source_lang
        self.target_lang = target_lang


class GenerationError(VoteWiseError):
    """Raised when Gemini fails to generate a valid response."""

    def __init__(self, reason: str) -> None:
        """Initialise GenerationError.

        Args:
            reason: Description of why generation failed.
        """
        super().__init__(
            message=f"Gemini generation failed: {reason}",
            code="GENERATION_ERROR",
        )


class ValidationError(VoteWiseError):
    """Raised when user-supplied input fails validation."""

    def __init__(self, field: str, reason: str) -> None:
        """Initialise ValidationError.

        Args:
            field: The input field that failed validation.
            reason: Why the field value is invalid.
        """
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            code="VALIDATION_ERROR",
        )
        self.field = field


class StorageError(VoteWiseError):
    """Raised when a Firestore or Cloud Storage operation fails."""

    def __init__(self, operation: str, reason: str) -> None:
        """Initialise StorageError.

        Args:
            operation: The storage operation that failed (e.g. 'write', 'read').
            reason: Reason the operation failed.
        """
        super().__init__(
            message=f"Storage operation '{operation}' failed: {reason}",
            code="STORAGE_ERROR",
        )
        self.operation = operation
