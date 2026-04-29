"""Election answer response model for VoteWise.

Defines the structured answer returned by the election assistant
after processing a user question.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["ElectionAnswer"]


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
