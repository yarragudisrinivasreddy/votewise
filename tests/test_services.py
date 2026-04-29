"""Tests for VoteWise service layer behaviour.

Validates that each service wrapper correctly delegates to its
underlying Google Cloud client, handles errors gracefully, and
returns well-formed models.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.exceptions import (
    GenerationError,
    StorageError,
    TranslationError,
    ServiceUnavailableError,
)
from app.models import ConversationTurn, ServiceHealth


# ────────────────────────────────────────────────────────────────────────────
# CloudTranslateService
# ────────────────────────────────────────────────────────────────────────────

class TestCloudTranslateService:
    @patch("app.services.translate.translate")
    def test_detect_language_returns_supported_code(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_lang = MagicMock()
        mock_lang.language_code = "hi"
        mock_client.detect_language.return_value.languages = [mock_lang]

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        result = svc.detect_language("मतदान")
        assert result == "hi"

    @patch("app.services.translate.translate")
    def test_detect_language_falls_back_on_unsupported(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_lang = MagicMock()
        mock_lang.language_code = "zz"  # unsupported
        mock_client.detect_language.return_value.languages = [mock_lang]

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        result = svc.detect_language("something")
        assert result == "en"  # DEFAULT_LANGUAGE

    @patch("app.services.translate.translate")
    def test_detect_language_raises_translation_error_on_api_failure(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_client.detect_language.side_effect = Exception("API error")

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        with pytest.raises(TranslationError):
            svc.detect_language("text")

    @patch("app.services.translate.translate")
    def test_translate_returns_translated_text(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_translation = MagicMock()
        mock_translation.translated_text = "मतदाता पंजीकरण"
        mock_client.translate_text.return_value.translations = [mock_translation]

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        result = svc.translate("Voter registration", "hi")
        assert result == "मतदाता पंजीकरण"

    @patch("app.services.translate.translate")
    def test_translate_empty_string_returns_empty(self, mock_translate_module):
        mock_translate_module.TranslationServiceClient.return_value = MagicMock()
        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        assert svc.translate("   ", "hi") == "   "

    @patch("app.services.translate.translate")
    def test_translate_uses_cache_on_second_call(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_translation = MagicMock()
        mock_translation.translated_text = "cached result"
        mock_client.translate_text.return_value.translations = [mock_translation]

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        svc.translate("hello", "hi")
        svc.translate("hello", "hi")
        # Client called only once due to cache
        assert mock_client.translate_text.call_count == 1

    @patch("app.services.translate.translate")
    def test_translate_raises_on_api_failure(self, mock_translate_module):
        mock_client = MagicMock()
        mock_translate_module.TranslationServiceClient.return_value = mock_client
        mock_client.translate_text.side_effect = Exception("quota exceeded")

        from app.services.translate import CloudTranslateService
        svc = CloudTranslateService("test-project")
        with pytest.raises(TranslationError):
            svc.translate("hello", "hi")


# ────────────────────────────────────────────────────────────────────────────
# FirestoreConversationStore
# ────────────────────────────────────────────────────────────────────────────

class TestFirestoreConversationStore:
    @patch("app.services.firestore.firestore")
    def test_load_history_returns_empty_for_new_session(self, mock_firestore):
        mock_client = MagicMock()
        mock_firestore.Client.return_value = mock_client
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        from app.services.firestore import FirestoreConversationStore
        store = FirestoreConversationStore("test-project")
        history = store.load_history("session-abc")
        assert history == []

    @patch("app.services.firestore.firestore")
    def test_load_history_returns_turns(self, mock_firestore):
        mock_client = MagicMock()
        mock_firestore.Client.return_value = mock_client
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "turns": [
                {"question": "Q1", "answer": "A1", "language": "en", "topic": "general"}
            ]
        }
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        from app.services.firestore import FirestoreConversationStore
        store = FirestoreConversationStore("test-project")
        history = store.load_history("session-abc")
        assert len(history) == 1
        assert history[0].question == "Q1"

    @patch("app.services.firestore.firestore")
    def test_append_turn_calls_set(self, mock_firestore):
        mock_client = MagicMock()
        mock_firestore.Client.return_value = mock_client
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value.exists = False
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        from app.services.firestore import FirestoreConversationStore
        store = FirestoreConversationStore("test-project")
        turn = ConversationTurn("Q", "A", "en", "general")
        store.append_turn("session-abc", turn)
        mock_doc_ref.set.assert_called_once()

    @patch("app.services.firestore.firestore")
    def test_load_history_raises_storage_error_on_failure(self, mock_firestore):
        mock_client = MagicMock()
        mock_firestore.Client.return_value = mock_client
        mock_client.collection.return_value.document.return_value.get.side_effect = Exception("DB error")

        from app.services.firestore import FirestoreConversationStore
        store = FirestoreConversationStore("test-project")
        with pytest.raises(StorageError):
            store.load_history("bad-session")

    @patch("app.services.firestore.firestore")
    def test_max_turns_trims_history(self, mock_firestore):
        mock_client = MagicMock()
        mock_firestore.Client.return_value = mock_client
        existing = [
            {"question": f"Q{i}", "answer": f"A{i}", "language": "en", "topic": "general"}
            for i in range(5)
        ]
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"turns": existing}
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_client.collection.return_value.document.return_value = mock_doc_ref

        from app.services.firestore import FirestoreConversationStore
        store = FirestoreConversationStore("test-project", max_turns=3)
        turn = ConversationTurn("Q_new", "A_new", "en", "general")
        store.append_turn("session", turn)

        saved_turns = mock_doc_ref.set.call_args[0][0]["turns"]
        assert len(saved_turns) == 3


# ────────────────────────────────────────────────────────────────────────────
# SecretManagerService
# ────────────────────────────────────────────────────────────────────────────

class TestSecretManagerService:
    @patch("app.services.secret_storage.secretmanager")
    def test_get_secret_returns_value(self, mock_sm):
        mock_client = MagicMock()
        mock_sm.SecretManagerServiceClient.return_value = mock_client
        mock_client.access_secret_version.return_value.payload.data = b"my-secret-value"

        from app.services.secret_storage import SecretManagerService
        svc = SecretManagerService("test-project")
        result = svc.get_secret("my-secret")
        assert result == "my-secret-value"

    @patch("app.services.secret_storage.secretmanager")
    def test_get_secret_raises_on_failure(self, mock_sm):
        mock_client = MagicMock()
        mock_sm.SecretManagerServiceClient.return_value = mock_client
        mock_client.access_secret_version.side_effect = Exception("not found")

        from app.services.secret_storage import SecretManagerService
        svc = SecretManagerService("test-project")
        with pytest.raises(ServiceUnavailableError):
            svc.get_secret("missing-secret")


# ────────────────────────────────────────────────────────────────────────────
# CloudStorageService
# ────────────────────────────────────────────────────────────────────────────

class TestCloudStorageService:
    @patch("app.services.secret_storage.storage")
    def test_archive_session_uploads_json(self, mock_storage):
        mock_client = MagicMock()
        mock_storage.Client.return_value = mock_client
        mock_blob = MagicMock()
        mock_client.bucket.return_value.blob.return_value = mock_blob

        from app.services.secret_storage import CloudStorageService
        svc = CloudStorageService("test-project", "test-bucket")
        svc.archive_session("session-123", {"key": "value"})
        mock_blob.upload_from_string.assert_called_once()

    @patch("app.services.secret_storage.storage")
    def test_archive_session_raises_storage_error_on_failure(self, mock_storage):
        mock_client = MagicMock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value.blob.return_value.upload_from_string.side_effect = Exception("upload fail")

        from app.services.secret_storage import CloudStorageService
        svc = CloudStorageService("test-project", "test-bucket")
        with pytest.raises(StorageError):
            svc.archive_session("session-123", {})

    @patch("app.services.secret_storage.storage")
    def test_archive_json_is_valid(self, mock_storage):
        mock_client = MagicMock()
        mock_storage.Client.return_value = mock_client
        mock_blob = MagicMock()
        mock_client.bucket.return_value.blob.return_value = mock_blob

        from app.services.secret_storage import CloudStorageService
        svc = CloudStorageService("test-project", "test-bucket")
        data = {"session": "abc", "turns": 3}
        svc.archive_session("abc", data)

        call_args = mock_blob.upload_from_string.call_args
        uploaded = call_args[0][0]
        parsed = json.loads(uploaded)
        assert parsed["session"] == "abc"


# ────────────────────────────────────────────────────────────────────────────
# GeminiService
# ────────────────────────────────────────────────────────────────────────────

class TestGeminiService:
    @patch("app.services.gemini.vertexai")
    @patch("app.services.gemini.GenerativeModel")
    def test_generate_returns_text(self, mock_model_cls, mock_vertexai):
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message.return_value.text = "  Here is your answer.  "

        from app.services.gemini import GeminiService
        svc = GeminiService("test-project")
        result = svc.generate("system", "user question", [])
        assert result == "Here is your answer."

    @patch("app.services.gemini.vertexai")
    @patch("app.services.gemini.GenerativeModel")
    def test_generate_raises_on_empty_response(self, mock_model_cls, mock_vertexai):
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message.return_value.text = "   "

        from app.services.gemini import GeminiService
        svc = GeminiService("test-project")
        with pytest.raises(GenerationError):
            svc.generate("system", "question", [])

    @patch("app.services.gemini.vertexai")
    @patch("app.services.gemini.GenerativeModel")
    def test_generate_raises_on_api_error(self, mock_model_cls, mock_vertexai):
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        mock_chat = MagicMock()
        mock_model.start_chat.return_value = mock_chat
        mock_chat.send_message.side_effect = Exception("quota exceeded")

        from app.services.gemini import GeminiService
        svc = GeminiService("test-project")
        with pytest.raises(GenerationError):
            svc.generate("system", "question", [])

    @patch("app.services.gemini.vertexai")
    @patch("app.services.gemini.GenerativeModel")
    def test_build_history_converts_turns(self, mock_model_cls, mock_vertexai):
        mock_model_cls.return_value = MagicMock()
        from app.services.gemini import GeminiService
        turns = [
            ConversationTurn("Q1", "A1", "en", "general"),
            ConversationTurn("Q2", "A2", "en", "evm_vvpat"),
        ]
        history = GeminiService._build_history(turns)
        # 2 turns → 4 Content objects (user + model per turn)
        assert len(history) == 4

    @patch("app.services.gemini.vertexai")
    @patch("app.services.gemini.GenerativeModel")
    def test_vertexai_init_called(self, mock_model_cls, mock_vertexai):
        mock_model_cls.return_value = MagicMock()
        from app.services.gemini import GeminiService
        GeminiService("my-project", region="asia-south1")
        mock_vertexai.init.assert_called_once_with(project="my-project", location="asia-south1")
