"""Application-wide constants and enumerations for VoteWise.

Centralises all string literals, numeric limits, and domain
values into typed, self-documenting enumerations. No magic
strings exist elsewhere in the codebase.
"""

from __future__ import annotations

__all__ = [
    "SupportedLanguage",
    "ElectionTopic",
    "HttpStatus",
    "MAX_QUESTION_LENGTH",
    "MAX_CONVERSATION_TURNS",
    "FIRESTORE_COLLECTION",
    "STORAGE_BUCKET_SUFFIX",
    "GEMINI_MODEL",
    "CLOUD_REGION",
    "DEFAULT_LANGUAGE",
    "GEMINI_MAX_OUTPUT_TOKENS",
    "GEMINI_TEMPERATURE",
]

from enum import Enum, unique


@unique
class SupportedLanguage(str, Enum):
    """BCP-47 codes for languages supported by VoteWise.

    Each value is a valid Cloud Translate v3 language code.
    The enum inherits from str so values are directly usable
    as dictionary keys and JSON-serialisable without conversion.
    """

    ENGLISH = "en"
    HINDI = "hi"
    TELUGU = "te"
    TAMIL = "ta"
    MARATHI = "mr"
    BENGALI = "bn"
    KANNADA = "kn"

    @classmethod
    def display_name(cls, code: str) -> str:
        """Return a human-readable display name for a language code.

        Args:
            code: A BCP-47 language code string.

        Returns:
            Display name, or the raw code if not found.
        """
        _display: dict[str, str] = {
            cls.ENGLISH: "English",
            cls.HINDI: "हिन्दी",
            cls.TELUGU: "తెలుగు",
            cls.TAMIL: "தமிழ்",
            cls.MARATHI: "मराठी",
            cls.BENGALI: "বাংলা",
            cls.KANNADA: "ಕನ್ನಡ",
        }
        return _display.get(code, code)

    @classmethod
    def values(cls) -> list[str]:
        """Return all supported BCP-47 language code strings.

        Returns:
            Sorted list of language code strings.
        """
        return sorted(member.value for member in cls)


@unique
class ElectionTopic(str, Enum):
    """High-level topics the election assistant can address."""

    VOTER_REGISTRATION = "voter_registration"
    HOW_TO_VOTE = "how_to_vote"
    ECI = "election_commission"
    EVM = "evm_vvpat"
    ELECTION_TYPES = "election_types"
    CONSTITUENCIES = "constituencies"
    TIMELINE = "election_timeline"
    PARTIES_SYMBOLS = "parties_and_symbols"
    NOTA = "nota"
    RESULTS = "results_and_counting"
    GENERAL = "general"


@unique
class HttpStatus(int, Enum):
    """Subset of HTTP status codes used by VoteWise responses."""

    OK = 200
    BAD_REQUEST = 400
    UNPROCESSABLE = 422
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ---------------------------------------------------------------------------
# Scalar limits
# ---------------------------------------------------------------------------

#: Maximum characters accepted per user question.
MAX_QUESTION_LENGTH: int = 1_000

#: Maximum number of conversation turns retained in Firestore per session.
MAX_CONVERSATION_TURNS: int = 20

#: Firestore collection name for conversation sessions.
FIRESTORE_COLLECTION: str = "election_sessions"

#: Cloud Storage bucket suffix for session logs.
STORAGE_BUCKET_SUFFIX: str = "-votewise-logs"

#: Gemini model identifier.
GEMINI_MODEL: str = "gemini-2.5-flash"

#: Google Cloud deployment region.
CLOUD_REGION: str = "asia-south1"

#: Default language when detection is inconclusive.
DEFAULT_LANGUAGE: str = SupportedLanguage.ENGLISH

#: Vertex AI API endpoint for asia-south1.
VERTEX_AI_ENDPOINT: str = f"https://{CLOUD_REGION}-aiplatform.googleapis.com"

#: Cache TTL in seconds for translated content.
TRANSLATE_CACHE_TTL: int = 3_600

#: Maximum tokens for Gemini response generation.
GEMINI_MAX_OUTPUT_TOKENS: int = 4_096

#: Temperature for Gemini — lower = more factual.
GEMINI_TEMPERATURE: float = 0.3
