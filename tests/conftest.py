"""Shared pytest fixtures for the VoteWise test suite."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.config import AppConfig
from app.models import ConversationTurn, ElectionAnswer, ServiceHealth


@pytest.fixture()
def sample_config() -> AppConfig:
    """Return a minimal valid AppConfig for testing."""
    return AppConfig(project_id="test-project")


@pytest.fixture()
def sample_turn() -> ConversationTurn:
    """Return a sample conversation turn."""
    return ConversationTurn(
        question="How do I register to vote?",
        answer="You can register at voters.eci.gov.in.",
        language="en",
        topic="voter_registration",
    )


@pytest.fixture()
def healthy_service() -> ServiceHealth:
    """Return a healthy ServiceHealth instance."""
    return ServiceHealth(name="test", healthy=True)


@pytest.fixture()
def unhealthy_service() -> ServiceHealth:
    """Return an unhealthy ServiceHealth instance."""
    return ServiceHealth(name="test", healthy=False, detail="Connection refused")


@pytest.fixture()
def mock_translate():
    """Mock CloudTranslateService."""
    svc = MagicMock()
    svc.detect_language.return_value = "en"
    svc.translate.side_effect = lambda text, lang: text
    svc.health.return_value = ServiceHealth(name="translate", healthy=True)
    return svc


@pytest.fixture()
def mock_gemini():
    """Mock GeminiService."""
    svc = MagicMock()
    svc.generate.return_value = "India's Election Commission oversees all elections."
    svc.health.return_value = ServiceHealth(name="gemini", healthy=True)
    return svc


@pytest.fixture()
def mock_store():
    """Mock FirestoreConversationStore."""
    svc = MagicMock()
    svc.load_history.return_value = []
    svc.append_turn.return_value = None
    svc.health.return_value = ServiceHealth(name="firestore", healthy=True)
    return svc


@pytest.fixture()
def mock_secret_manager():
    """Mock SecretManagerService."""
    svc = MagicMock()
    svc.health.return_value = ServiceHealth(name="secret_manager", healthy=True)
    return svc


@pytest.fixture()
def mock_storage():
    """Mock CloudStorageService."""
    svc = MagicMock()
    svc.health.return_value = ServiceHealth(name="storage", healthy=True)
    return svc


@pytest.fixture()
def app(mock_translate, mock_gemini, mock_store, mock_secret_manager, mock_storage):
    """Create a test Flask application with all services mocked."""
    with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
        with (
            patch("app.services.gemini.GeminiService", return_value=mock_gemini),
            patch("app.services.translate.CloudTranslateService", return_value=mock_translate),
            patch("app.services.firestore.FirestoreConversationStore", return_value=mock_store),
            patch("app.services.secret_storage.SecretManagerService", return_value=mock_secret_manager),
            patch("app.services.secret_storage.CloudStorageService", return_value=mock_storage),
            patch("vertexai.init"),
        ):
            from app import create_app
            flask_app = create_app()
            flask_app.config["TESTING"] = True
            flask_app.config["TRANSLATE"] = mock_translate
            flask_app.config["GEMINI"] = mock_gemini
            flask_app.config["FIRESTORE"] = mock_store
            flask_app.config["SECRET_MANAGER"] = mock_secret_manager
            flask_app.config["STORAGE"] = mock_storage
            yield flask_app


@pytest.fixture()
def client(app):
    """Return a test client for the Flask application."""
    return app.test_client()
