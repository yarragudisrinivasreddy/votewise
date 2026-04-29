"""Protocol interfaces for all VoteWise service layer components.

Defines structural subtypes (PEP 544) that decouple the application
logic from concrete service implementations, enabling dependency
injection and straightforward unit-test mocking without inheritance.
"""

from __future__ import annotations

__all__ = [
    "TranslationService",
    "GenerationService",
    "ConversationStore",
]

from typing import Protocol, runtime_checkable

from app.models import ConversationTurn, ServiceHealth


@runtime_checkable
class TranslationService(Protocol):
    """Protocol for a text translation service."""

    def detect_language(self, text: str) -> str:
        """Detect the BCP-47 language code of ``text``.

        Args:
            text: The text whose language should be detected.

        Returns:
            A BCP-47 language code string (e.g. ``'hi'``).
        """
        raise NotImplementedError

    def translate(self, text: str, target_language: str) -> str:
        """Translate ``text`` into ``target_language``.

        Args:
            text: Source text to translate.
            target_language: BCP-47 target language code.

        Returns:
            Translated text in the target language.
        """
        raise NotImplementedError

    def health(self) -> ServiceHealth:
        """Return a health snapshot for this service.

        Returns:
            A :class:`~app.models.ServiceHealth` instance.
        """
        raise NotImplementedError


@runtime_checkable
class GenerationService(Protocol):
    """Protocol for a text generation (LLM) service."""

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[ConversationTurn],
    ) -> str:
        """Generate a response given a prompt and conversation history.

        Args:
            system_prompt: Instructions defining the assistant's behaviour.
            user_prompt: The current user query.
            history: Prior conversation turns for context.

        Returns:
            The generated response text.
        """
        raise NotImplementedError

    def health(self) -> ServiceHealth:
        """Return a health snapshot for this service.

        Returns:
            A :class:`~app.models.ServiceHealth` instance.
        """
        raise NotImplementedError


@runtime_checkable
class ConversationStore(Protocol):
    """Protocol for persisting and retrieving conversation history."""

    def load_history(self, session_id: str) -> list[ConversationTurn]:
        """Load conversation history for ``session_id``.

        Args:
            session_id: The anonymised session identifier.

        Returns:
            List of :class:`~app.models.ConversationTurn` objects,
            ordered oldest to newest.
        """
        raise NotImplementedError

    def append_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Append a new turn to the session history.

        Args:
            session_id: The anonymised session identifier.
            turn: The :class:`~app.models.ConversationTurn` to append.
        """
        raise NotImplementedError

    def health(self) -> ServiceHealth:
        """Return a health snapshot for this service.

        Returns:
            A :class:`~app.models.ServiceHealth` instance.
        """
        raise NotImplementedError
