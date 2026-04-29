"""Conversation turn model for VoteWise.

Represents a single question-answer exchange within a conversation
session, used for both Firestore persistence and Gemini context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["ConversationTurn"]


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
