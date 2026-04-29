"""Application configuration management for VoteWise.

Loads settings from environment variables with explicit validation,
ensuring the app fails fast with clear messages rather than
producing cryptic runtime errors.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from app.constants import (
    CLOUD_REGION,
    FIRESTORE_COLLECTION,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    MAX_CONVERSATION_TURNS,
    MAX_QUESTION_LENGTH,
    STORAGE_BUCKET_SUFFIX,
    TRANSLATE_CACHE_TTL,
)
from app.exceptions import ConfigurationError


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration.

    All fields are populated at startup from environment variables.
    The dataclass is frozen to prevent accidental mutation at runtime.
    """

    project_id: str
    region: str = CLOUD_REGION
    gemini_model: str = GEMINI_MODEL
    gemini_temperature: float = GEMINI_TEMPERATURE
    gemini_max_tokens: int = GEMINI_MAX_OUTPUT_TOKENS
    firestore_collection: str = FIRESTORE_COLLECTION
    storage_bucket_suffix: str = STORAGE_BUCKET_SUFFIX
    translate_cache_ttl: int = TRANSLATE_CACHE_TTL
    max_question_length: int = MAX_QUESTION_LENGTH
    max_conversation_turns: int = MAX_CONVERSATION_TURNS
    debug: bool = False
    allowed_origins: list[str] = field(default_factory=list)

    @property
    def storage_bucket(self) -> str:
        """Derive the Cloud Storage bucket name from the project ID.

        Returns:
            Full bucket name string.
        """
        return f"{self.project_id}{self.storage_bucket_suffix}"

    @property
    def vertex_ai_location(self) -> str:
        """Return the Vertex AI location matching the deployment region.

        Returns:
            Vertex AI location string.
        """
        return self.region


def load_config() -> AppConfig:
    """Load and validate application configuration from the environment.

    Reads environment variables and constructs an :class:`AppConfig`
    instance. Raises :class:`~app.exceptions.ConfigurationError` for
    any missing required variable.

    Returns:
        A fully-populated, validated :class:`AppConfig`.

    Raises:
        ConfigurationError: If ``GOOGLE_CLOUD_PROJECT`` is not set.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project_id:
        raise ConfigurationError("GOOGLE_CLOUD_PROJECT")

    debug_raw = os.getenv("DEBUG", "false").lower()
    debug = debug_raw in {"1", "true", "yes"}

    origins_raw = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

    return AppConfig(
        project_id=project_id,
        region=os.getenv("CLOUD_REGION", CLOUD_REGION),
        debug=debug,
        allowed_origins=origins,
    )
