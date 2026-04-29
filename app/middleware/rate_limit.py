"""Rate limiting middleware for VoteWise.

Applies per-IP rate limits to the API endpoints using Flask-Limiter
to prevent abuse and ensure fair resource usage across users.
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

#: Shared Limiter instance — attached to the app in :func:`register_rate_limiter`.
limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def register_rate_limiter(app: Flask) -> None:
    """Initialise and register the rate limiter with ``app``.

    Attaches a custom error handler so limit violations return JSON
    rather than the default HTML response.

    Args:
        app: The Flask application instance.
    """
    limiter.init_app(app)

    @app.errorhandler(429)
    def rate_limit_exceeded(_exc):
        """Return a structured JSON response for rate limit violations."""
        logger.warning("Rate limit exceeded", extra={"remote": get_remote_address()})
        return (
            jsonify(
                {
                    "error": "Too many requests. Please wait before trying again.",
                    "code": "RATE_LIMIT_EXCEEDED",
                }
            ),
            429,
        )
