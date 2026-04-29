"""Google Cloud Natural Language sentiment analysis service for VoteWise.

Analyses the sentiment of user questions to detect frustration,
confusion, or urgency, enabling more empathetic response generation.
"""

from __future__ import annotations

__all__ = ["SentimentResult", "NaturalLanguageService"]

import logging
from dataclasses import dataclass

from google.cloud import language_v1

from app.models.health import ServiceHealth

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SentimentResult:
    """Result of a Cloud Natural Language sentiment analysis call.

    Attributes:
        score: Sentiment score from -1.0 (negative) to +1.0 (positive).
        magnitude: Overall strength of sentiment regardless of sign.
        label: Human-readable sentiment label derived from score.
    """

    score: float
    magnitude: float

    @property
    def label(self) -> str:
        """Derive a human-readable sentiment label from the score.

        Returns:
            One of ``'positive'``, ``'neutral'``, or ``'negative'``.
        """
        if self.score >= 0.25:
            return "positive"
        if self.score <= -0.25:
            return "negative"
        return "neutral"

    def to_dict(self) -> dict[str, float | str]:
        """Serialise to a plain dictionary.

        Returns:
            Dictionary with ``score``, ``magnitude``, and ``label``.
        """
        return {
            "score": self.score,
            "magnitude": self.magnitude,
            "label": self.label,
        }


class NaturalLanguageService:
    """Google Cloud Natural Language API service for sentiment analysis.

    Used to detect the emotional tone of user questions, allowing VoteWise
    to tailor response empathy to the user's apparent state of mind.

    Args:
        project_id: Google Cloud project identifier.
    """

    def __init__(self, project_id: str) -> None:
        self._client = language_v1.LanguageServiceClient()
        self._project_id = project_id
        logger.info("NaturalLanguageService initialised", extra={"project": project_id})

    def analyse_sentiment(self, text: str) -> SentimentResult:
        """Analyse the sentiment of ``text`` using Cloud Natural Language.

        Args:
            text: The text to analyse (user question or message body).

        Returns:
            A :class:`SentimentResult` with score and magnitude.
        """
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT,
        )
        try:
            response = self._client.analyze_sentiment(
                request={"document": document}
            )
            sentiment = response.document_sentiment
            result = SentimentResult(
                score=round(sentiment.score, 4),
                magnitude=round(sentiment.magnitude, 4),
            )
            logger.info(
                "Sentiment analysed",
                extra={"label": result.label, "score": result.score},
            )
            return result
        except Exception:  # pylint: disable=broad-exception-caught
            # Graceful degradation — return neutral on API failure.
            logger.warning("Sentiment analysis failed; returning neutral")
            return SentimentResult(score=0.0, magnitude=0.0)

    def health(self) -> ServiceHealth:
        """Probe Cloud Natural Language with a minimal request.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            self.analyse_sentiment("test")
            return ServiceHealth(name="natural_language", healthy=True)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return ServiceHealth(name="natural_language", healthy=False, detail=str(exc))
