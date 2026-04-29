"""Security utilities for VoteWise.

Provides input sanitisation, validation, and rate-limiting helpers.
All user-supplied data must pass through this module before reaching
any service layer component.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from typing import Final

from app.constants import MAX_QUESTION_LENGTH, SupportedLanguage
from app.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Compile expensive patterns once at import time.
# ---------------------------------------------------------------------------

#: Detects runs of whitespace characters (including newlines).
_WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")

#: Detects ASCII control characters (excluding tab, newline, carriage-return).
_CONTROL_CHAR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)

#: Detects potential prompt-injection sequences.
_INJECTION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(ignore\s+previous|disregard\s+instructions|system\s*prompt|jailbreak)",
    re.IGNORECASE,
)


def sanitise_question(raw: str) -> str:
    """Sanitise and normalise a raw user question.

    Applies the following transformations in order:
    1. Strip leading/trailing whitespace.
    2. Collapse internal whitespace runs to a single space.
    3. Remove ASCII control characters.
    4. HTML-escape any markup characters.
    5. Apply Unicode NFC normalisation.

    Args:
        raw: Unsanitised user input string.

    Returns:
        The sanitised, normalised question string.

    Raises:
        ValidationError: If ``raw`` is empty after sanitisation,
            or exceeds :data:`~app.constants.MAX_QUESTION_LENGTH`.
    """
    if not isinstance(raw, str):
        raise ValidationError("question", "Must be a string value.")

    text = _WHITESPACE_PATTERN.sub(" ", raw).strip()
    text = _CONTROL_CHAR_PATTERN.sub("", text)
    text = html.escape(text, quote=False)
    text = unicodedata.normalize("NFC", text)

    if not text:
        raise ValidationError("question", "Question must not be empty.")

    if len(text) > MAX_QUESTION_LENGTH:
        raise ValidationError(
            "question",
            f"Question exceeds the maximum length of {MAX_QUESTION_LENGTH} characters.",
        )

    if _INJECTION_PATTERN.search(text):
        raise ValidationError("question", "Question contains disallowed content.")

    return text


def validate_language_code(code: str) -> str:
    """Validate that a language code is supported by VoteWise.

    Args:
        code: A BCP-47 language code string supplied by the client.

    Returns:
        The validated language code (unchanged).

    Raises:
        ValidationError: If the code is not in :class:`~app.constants.SupportedLanguage`.
    """
    if code not in SupportedLanguage.values():
        raise ValidationError(
            "language",
            f"'{code}' is not a supported language. "
            f"Supported codes: {SupportedLanguage.values()}",
        )
    return code


def derive_session_id(ip_address: str, user_agent: str) -> str:
    """Derive a deterministic, anonymised session identifier.

    The identifier is a SHA-256 digest of the concatenated IP address
    and User-Agent header, truncated to 16 hex characters. No PII is
    stored or logged.

    Args:
        ip_address: The client's remote IP address.
        user_agent: The client's User-Agent header value.

    Returns:
        A 16-character hexadecimal session ID string.
    """
    raw = f"{ip_address}|{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
