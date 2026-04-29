"""Typed data models for VoteWise API requests and responses.

Uses :mod:`dataclasses` with full type annotations to provide
self-documenting, IDE-friendly contracts for all API surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestionRequest:
    """Validated payload for the /api/ask endpoint.

    Attributes:
        question: The sanitised user question text.
        language: BCP-47 language code for the response.
        session_id: Anonymised session identifier for conversation history.
    """

    question: str
    language: str
    session_id: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


@dataclass
class ElectionAnswer:
    """Structured answer returned by the election assistant.

    Attributes:
        answer: The main response text in the requested language.
        topic: Detected election topic category (from ElectionTopic enum).
        language: BCP-47 code of the language used in ``answer``.
        suggested_questions: Follow-up questions to encourage exploration.
        sources: Optional references for further reading.
    """

    answer: str
    topic: str
    language: str
    suggested_questions: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary for JSON responses.

        Returns:
            Dictionary with all public fields.
        """
        return {
            "answer": self.answer,
            "topic": self.topic,
            "language": self.language,
            "suggested_questions": self.suggested_questions,
            "sources": self.sources,
        }


@dataclass
class ConversationTurn:
    """A single question-answer turn in a conversation session.

    Attributes:
        question: The user's original question.
        answer: The assistant's answer text.
        language: Language code used for the answer.
        topic: Detected topic category.
    """

    question: str
    answer: str
    language: str
    topic: str

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary for Firestore storage.

        Returns:
            Dictionary representation of this turn.
        """
        return {
            "question": self.question,
            "answer": self.answer,
            "language": self.language,
            "topic": self.topic,
        }


@dataclass
class ServiceHealth:
    """Health status of a single external service dependency.

    Attributes:
        name: Service name (e.g. 'firestore', 'translate').
        healthy: Whether the service is reachable and functional.
        detail: Optional additional context (e.g. error message).
    """

    name: str
    healthy: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary.

        Returns:
            Dictionary with ``name``, ``healthy``, and ``detail``.
        """
        return {"name": self.name, "healthy": self.healthy, "detail": self.detail}
