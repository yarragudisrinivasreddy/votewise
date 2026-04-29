"""Tests for app.exceptions module."""

from __future__ import annotations

import pytest

from app.exceptions import (
    ConfigurationError,
    GenerationError,
    ServiceUnavailableError,
    StorageError,
    TranslationError,
    ValidationError,
    VoteWiseError,
)


class TestVoteWiseError:
    def test_is_exception(self):
        assert issubclass(VoteWiseError, Exception)

    def test_message_stored(self):
        err = VoteWiseError("test message")
        assert err.message == "test message"

    def test_default_code(self):
        err = VoteWiseError("msg")
        assert err.code == "INTERNAL_ERROR"

    def test_custom_code(self):
        err = VoteWiseError("msg", code="CUSTOM")
        assert err.code == "CUSTOM"

    def test_repr(self):
        err = VoteWiseError("msg", "CODE")
        assert "VoteWiseError" in repr(err)
        assert "msg" in repr(err)


class TestConfigurationError:
    def test_inherits_votewise(self):
        assert issubclass(ConfigurationError, VoteWiseError)

    def test_key_stored(self):
        err = ConfigurationError("MY_KEY")
        assert err.key == "MY_KEY"

    def test_code_is_configuration_error(self):
        err = ConfigurationError("X")
        assert err.code == "CONFIGURATION_ERROR"

    def test_message_contains_key(self):
        err = ConfigurationError("SECRET_KEY")
        assert "SECRET_KEY" in err.message


class TestServiceUnavailableError:
    def test_service_stored(self):
        err = ServiceUnavailableError("firestore", "timeout")
        assert err.service == "firestore"

    def test_reason_stored(self):
        err = ServiceUnavailableError("gemini", "quota exceeded")
        assert err.reason == "quota exceeded"

    def test_code(self):
        err = ServiceUnavailableError("x", "y")
        assert err.code == "SERVICE_UNAVAILABLE"


class TestTranslationError:
    def test_source_lang_stored(self):
        err = TranslationError("hi", "en", "failed")
        assert err.source_lang == "hi"

    def test_target_lang_stored(self):
        err = TranslationError("hi", "en", "failed")
        assert err.target_lang == "en"

    def test_code(self):
        err = TranslationError("a", "b", "c")
        assert err.code == "TRANSLATION_ERROR"


class TestGenerationError:
    def test_message(self):
        err = GenerationError("quota hit")
        assert "quota hit" in err.message

    def test_code(self):
        err = GenerationError("x")
        assert err.code == "GENERATION_ERROR"


class TestValidationError:
    def test_field_stored(self):
        err = ValidationError("question", "too long")
        assert err.field == "question"

    def test_code(self):
        err = ValidationError("q", "r")
        assert err.code == "VALIDATION_ERROR"


class TestStorageError:
    def test_operation_stored(self):
        err = StorageError("write", "disk full")
        assert err.operation == "write"

    def test_code(self):
        err = StorageError("read", "not found")
        assert err.code == "STORAGE_ERROR"
