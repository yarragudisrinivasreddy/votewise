"""VoteWise Flask application factory.

Creates and configures the Flask application using the app-factory
pattern. All service dependencies are initialised once and stored on
the application context, preventing repeated cold-starts.
"""

from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from app.config import load_config
from app.logging_config import configure_logging


def create_app() -> Flask:
    """Create and configure the VoteWise Flask application.

    Applies the following steps in order:
    1. Configure structured logging.
    2. Load and validate application configuration.
    3. Initialise all Google Cloud service clients.
    4. Register API and health-check Blueprints.
    5. Register global error handlers.

    Returns:
        A fully configured :class:`flask.Flask` application instance.
    """
    configure_logging()
    logger = logging.getLogger(__name__)

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    config = load_config()

    app.config["VOTEWISE_CONFIG"] = config
    app.config["DEBUG"] = config.debug

    CORS(app, origins=config.allowed_origins or ["*"])

    _register_services(app, config)
    _register_blueprints(app)
    _register_error_handlers(app)

    logger.info(
        "VoteWise application started",
        extra={"project": config.project_id, "region": config.region},
    )
    return app


def _register_services(app: Flask, config) -> None:
    """Initialise Google Cloud service clients and store on app context.

    Args:
        app: The Flask application instance.
        config: The loaded :class:`~app.config.AppConfig`.
    """
    from app.services.gemini import GeminiService
    from app.services.translate import CloudTranslateService
    from app.services.firestore import FirestoreConversationStore
    from app.services.secret_storage import SecretManagerService, CloudStorageService

    app.config["GEMINI"] = GeminiService(
        project_id=config.project_id,
        region=config.region,
    )
    app.config["TRANSLATE"] = CloudTranslateService(
        project_id=config.project_id,
        cache_ttl=config.translate_cache_ttl,
    )
    app.config["FIRESTORE"] = FirestoreConversationStore(
        project_id=config.project_id,
        collection=config.firestore_collection,
        max_turns=config.max_conversation_turns,
    )
    app.config["SECRET_MANAGER"] = SecretManagerService(project_id=config.project_id)
    app.config["STORAGE"] = CloudStorageService(
        project_id=config.project_id,
        bucket_name=config.storage_bucket,
    )


def _register_blueprints(app: Flask) -> None:
    """Register all route Blueprints with the application.

    Args:
        app: The Flask application instance.
    """
    from app.routes.api import api_bp
    from app.routes.health import health_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(health_bp)


def _register_error_handlers(app: Flask) -> None:
    """Register global exception handlers for clean JSON error responses.

    Args:
        app: The Flask application instance.
    """
    from flask import jsonify

    from app.exceptions import ValidationError, VoteWiseError

    @app.errorhandler(VoteWiseError)
    def handle_app_error(exc: VoteWiseError):
        return jsonify({"error": exc.message, "code": exc.code}), 400

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return jsonify({"error": exc.message, "code": exc.code, "field": exc.field}), 422

    @app.errorhandler(404)
    def handle_not_found(_exc):
        return jsonify({"error": "Resource not found.", "code": "NOT_FOUND"}), 404

    @app.errorhandler(500)
    def handle_internal(_exc):
        return jsonify({"error": "Internal server error.", "code": "INTERNAL_ERROR"}), 500
