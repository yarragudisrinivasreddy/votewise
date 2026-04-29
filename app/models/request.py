"""Request model for the VoteWise API.

Defines the validated, immutable payload structure for the
``/api/ask`` endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["QuestionRequest"]


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
