"""Cloud Translate v3 service for VoteWise.

Wraps the Google Cloud Translation API (v3) to provide language
detection and text translation. Results are cached in-process to
avoid redundant API calls for repeated identical inputs.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Final

from google.cloud import translate_v3 as translate

from app.constants import DEFAULT_LANGUAGE, TRANSLATE_CACHE_TTL, SupportedLanguage
from app.exceptions import TranslationError
from app.models import ServiceHealth

logger = logging.getLogger(__name__)

#: Sentinel value for cache entries that are past their TTL.
_CACHE_MISS: Final[object] = object()


class _CacheEntry:
    """Lightweight TTL-aware cache entry."""

    __slots__ = ("value", "expires_at")

    def __init__(self, value: str, ttl: int) -> None:
        self.value = value
        self.expires_at = time.monotonic() + ttl

    @property
    def expired(self) -> bool:
        """Return True if this entry has passed its TTL."""
        return time.monotonic() > self.expires_at


class CloudTranslateService:
    """Google Cloud Translation v3 service with in-process TTL cache.

    Thread-safe: uses a :class:`threading.Lock` to protect the cache
    dictionary from concurrent modifications.

    Args:
        project_id: Google Cloud project identifier.
        cache_ttl: Time-to-live in seconds for cached translations.
    """

    def __init__(self, project_id: str, cache_ttl: int = TRANSLATE_CACHE_TTL) -> None:
        self._project_id = project_id
        self._parent: str = f"projects/{project_id}/locations/global"
        self._client = translate.TranslationServiceClient()
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()
        self._cache_ttl = cache_ttl

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def detect_language(self, text: str) -> str:
        """Detect the BCP-47 language of ``text`` via Cloud Translate.

        Falls back to :data:`~app.constants.DEFAULT_LANGUAGE` when the
        detected language is not in the supported set.

        Args:
            text: The text whose language should be detected.

        Returns:
            A BCP-47 language code string.

        Raises:
            TranslationError: If the API call fails.
        """
        try:
            response = self._client.detect_language(
                parent=self._parent,
                content=text[:500],  # API limit; full text unnecessary.
                mime_type="text/plain",
            )
            detected = response.languages[0].language_code if response.languages else ""
            if detected in SupportedLanguage.values():
                logger.info("Language detected", extra={"lang": detected})
                return detected
            logger.info(
                "Unsupported language detected; falling back",
                extra={"detected": detected, "fallback": DEFAULT_LANGUAGE},
            )
            return DEFAULT_LANGUAGE
        except Exception as exc:
            raise TranslationError("auto", DEFAULT_LANGUAGE, str(exc)) from exc

    def translate(self, text: str, target_language: str) -> str:
        """Translate ``text`` into ``target_language``.

        Results are stored in an in-process TTL cache to avoid
        duplicate API calls for identical inputs.

        Args:
            text: Source text to translate.
            target_language: BCP-47 target language code.

        Returns:
            Translated text.

        Raises:
            TranslationError: If the API call fails.
        """
        if not text.strip():
            return text

        cache_key = f"{hash(text)}:{target_language}"
        cached = self._read_cache(cache_key)
        if cached is not _CACHE_MISS:
            return cached  # type: ignore[return-value]

        try:
            response = self._client.translate_text(
                parent=self._parent,
                contents=[text],
                target_language_code=target_language,
                mime_type="text/plain",
            )
            result = response.translations[0].translated_text
            self._write_cache(cache_key, result)
            logger.info(
                "Translation complete",
                extra={"target": target_language, "chars": len(result)},
            )
            return result
        except Exception as exc:
            raise TranslationError("auto", target_language, str(exc)) from exc

    def health(self) -> ServiceHealth:
        """Probe Cloud Translate by attempting a minimal detection call.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            self.detect_language("hello")
            return ServiceHealth(name="translate", healthy=True)
        except Exception as exc:  # noqa: BLE001
            return ServiceHealth(name="translate", healthy=False, detail=str(exc))

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _read_cache(self, key: str) -> object:
        """Return the cached value for ``key``, or ``_CACHE_MISS``."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expired:
                return _CACHE_MISS
            return entry.value

    def _write_cache(self, key: str, value: str) -> None:
        """Write ``value`` into the cache under ``key``."""
        with self._lock:
            self._cache[key] = _CacheEntry(value, self._cache_ttl)
