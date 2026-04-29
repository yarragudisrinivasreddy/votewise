"""Security middleware for VoteWise.

Applies HTTP security headers to every response following OWASP
recommendations for modern web applications. Headers are injected
via an after_request hook registered on the Flask application.
"""

from __future__ import annotations

__all__ = ["register_security_middleware"]

import logging

from flask import Flask, Response

logger = logging.getLogger(__name__)

#: Content Security Policy — restricts resource origins to self + Google Fonts.
_CSP: str = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)

#: Security headers applied to every response.
_SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": _CSP,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "geolocation=(), microphone=(), camera=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    ),
    "X-XSS-Protection": "1; mode=block",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
}


def _apply_security_headers(response: Response) -> Response:
    """Attach all OWASP-recommended security headers to ``response``.

    Args:
        response: The outgoing Flask :class:`~flask.Response` object.

    Returns:
        The same response with security headers attached.
    """
    for header, value in _SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


def register_security_middleware(app: Flask) -> None:
    """Register security header middleware with the Flask application.

    Attaches an ``after_request`` hook that injects all OWASP-recommended
    HTTP security headers into every outgoing response.

    Args:
        app: The Flask application instance.
    """

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        """Inject security headers into every outgoing response."""
        return _apply_security_headers(response)
