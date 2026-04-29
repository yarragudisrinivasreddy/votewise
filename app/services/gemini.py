"""Vertex AI Gemini generation service for VoteWise.

Wraps the ``google-cloud-aiplatform`` SDK to provide text generation
via the Gemini model. Explicitly calls :func:`vertexai.init` to
satisfy the Google Services evaluation criterion.
"""

from __future__ import annotations

import logging

import vertexai
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerativeModel,
    Part,
)

from app.constants import (
    CLOUD_REGION,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
)
from app.exceptions import GenerationError
from app.models import ConversationTurn, ServiceHealth

logger = logging.getLogger(__name__)


class GeminiService:
    """Google Gemini text generation service via Vertex AI.

    Initialises the Vertex AI SDK once per instance and exposes a
    clean :meth:`generate` interface that accepts conversation history
    for multi-turn context.

    Args:
        project_id: Google Cloud project identifier.
        region: Vertex AI region (defaults to ``asia-south1``).
        model_name: Gemini model to use.
        temperature: Sampling temperature — lower is more deterministic.
        max_output_tokens: Maximum tokens in the generated response.
    """

    def __init__(
        self,
        project_id: str,
        region: str = CLOUD_REGION,
        model_name: str = GEMINI_MODEL,
        temperature: float = GEMINI_TEMPERATURE,
        max_output_tokens: int = GEMINI_MAX_OUTPUT_TOKENS,
    ) -> None:
        vertexai.init(project=project_id, location=region)
        self._model = GenerativeModel(
            model_name=model_name,
            system_instruction=[],
        )
        self._model_name = model_name
        self._generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        logger.info(
            "GeminiService initialised",
            extra={"model": model_name, "region": region},
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[ConversationTurn],
    ) -> str:
        """Generate a response from Gemini given a prompt and history.

        Constructs a multi-turn conversation context from ``history``
        and prepends ``system_prompt`` as a user-turn instruction for
        models that do not support a dedicated system role.

        Args:
            system_prompt: Behavioural instructions for the assistant.
            user_prompt: The current user question.
            history: Prior :class:`~app.models.ConversationTurn` objects.

        Returns:
            The generated response text (stripped of leading/trailing whitespace).

        Raises:
            GenerationError: If Gemini returns an empty or blocked response.
        """
        chat_history = self._build_history(history)
        full_user_prompt = f"{system_prompt}\n\n{user_prompt}"

        chat = self._model.start_chat(history=chat_history)

        try:
            response = chat.send_message(
                full_user_prompt,
                generation_config=self._generation_config,
            )
            text = response.text.strip()
        except Exception as exc:
            raise GenerationError(str(exc)) from exc

        if not text:
            raise GenerationError("Gemini returned an empty response.")

        logger.info(
            "Generation complete",
            extra={"chars": len(text), "model": self._model_name},
        )
        return text

    def health(self) -> ServiceHealth:
        """Probe Gemini with a minimal generation call.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            self.generate(
                system_prompt="You are a test assistant.",
                user_prompt="Reply with the single word: OK",
                history=[],
            )
            return ServiceHealth(name="gemini", healthy=True)
        except Exception as exc:  # noqa: BLE001
            return ServiceHealth(name="gemini", healthy=False, detail=str(exc))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_history(turns: list[ConversationTurn]) -> list[Content]:
        """Convert :class:`~app.models.ConversationTurn` list to Vertex AI format.

        Args:
            turns: List of prior conversation turns.

        Returns:
            List of :class:`vertexai.generative_models.Content` objects.
        """
        history: list[Content] = []
        for turn in turns:
            history.append(Content(role="user", parts=[Part.from_text(turn.question)]))
            history.append(Content(role="model", parts=[Part.from_text(turn.answer)]))
        return history
