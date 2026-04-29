"""Firestore-backed conversation history store for VoteWise.

Persists and retrieves multi-turn conversation histories using
Google Cloud Firestore as the backing store.
"""

from __future__ import annotations

import logging

from google.cloud import firestore

from app.constants import FIRESTORE_COLLECTION, MAX_CONVERSATION_TURNS
from app.exceptions import StorageError
from app.models import ConversationTurn, ServiceHealth

logger = logging.getLogger(__name__)


class FirestoreConversationStore:
    """Persists conversation turns in Firestore.

    Each session is stored as a single Firestore document with an
    array field of turn dictionaries. Older turns are trimmed to
    :data:`~app.constants.MAX_CONVERSATION_TURNS` to bound document size.

    Args:
        project_id: Google Cloud project identifier.
        collection: Firestore collection name.
        max_turns: Maximum number of turns to retain per session.
    """

    _TURNS_FIELD: str = "turns"

    def __init__(
        self,
        project_id: str,
        collection: str = FIRESTORE_COLLECTION,
        max_turns: int = MAX_CONVERSATION_TURNS,
    ) -> None:
        self._client = firestore.Client(project=project_id)
        self._collection = collection
        self._max_turns = max_turns

    def load_history(self, session_id: str) -> list[ConversationTurn]:
        """Load conversation history for ``session_id`` from Firestore.

        Args:
            session_id: The anonymised session identifier.

        Returns:
            List of :class:`~app.models.ConversationTurn`, oldest first.
            Returns an empty list if the session does not exist.

        Raises:
            StorageError: If the Firestore read operation fails.
        """
        try:
            doc = self._collection_ref().document(session_id).get()
            if not doc.exists:
                return []
            raw_turns: list[dict] = doc.to_dict().get(self._TURNS_FIELD, [])
            return [
                ConversationTurn(
                    question=t["question"],
                    answer=t["answer"],
                    language=t["language"],
                    topic=t["topic"],
                )
                for t in raw_turns
            ]
        except Exception as exc:
            raise StorageError("read", str(exc)) from exc

    def append_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Append ``turn`` to the session history in Firestore.

        Trims the stored turns to :attr:`_max_turns` after appending,
        keeping only the most recent interactions.

        Args:
            session_id: The anonymised session identifier.
            turn: The conversation turn to append.

        Raises:
            StorageError: If the Firestore write operation fails.
        """
        try:
            existing = self.load_history(session_id)
            updated = (existing + [turn])[-self._max_turns :]
            self._collection_ref().document(session_id).set(
                {self._TURNS_FIELD: [t.to_dict() for t in updated]}
            )
            logger.info(
                "Turn appended",
                extra={"session": session_id, "turns": len(updated)},
            )
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("write", str(exc)) from exc

    def health(self) -> ServiceHealth:
        """Probe Firestore with a non-destructive read.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            self._collection_ref().limit(1).get()
            return ServiceHealth(name="firestore", healthy=True)
        except Exception as exc:  # noqa: BLE001
            return ServiceHealth(name="firestore", healthy=False, detail=str(exc))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collection_ref(self) -> firestore.CollectionReference:
        """Return a reference to the Firestore collection.

        Returns:
            A :class:`google.cloud.firestore.CollectionReference`.
        """
        return self._client.collection(self._collection)
