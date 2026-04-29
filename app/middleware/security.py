"""Security middleware for VoteWise.

Applies HTTP security headers to every response and enforces
origin validation on state-changing API endpoints. All headers
follow OWASP recommendations for modern web applications.
"""

from __future__ import annotations

import logging

from flask import Flask, Request, Response, request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security header values
# ---------------------------------------------------------------------------

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


def _validate_api_origin(req: Request) -> bool:
    """Validate that a state-changing API request originates from an allowed source.

    Checks the ``Origin`` or ``Referer`` header against the request host.
    Requests without either header (e.g. server-to-server) are permitted.

    Args:
        req: The incoming Flask :class:`~flask.Request`.

    Returns:
        True if the request is from an allowed origin, False otherwise.
    """
    origin = req.headers.get("Origin", "")
    referer = req.headers.get("Referer", "")
    host = req.host

    if not origin and not referer:
        # No browser context — allow (e.g. curl, server calls).
        return True

    source = origin or referer
    return host in source


def register_security_middleware(app: Flask) -> None:
    """Register all security middleware hooks with the Flask application.

    Attaches:
    - ``after_request``: injects security headers into every response.
    - ``before_request``: validates Origin header on POST/PUT/DELETE endpoints.

    Args:
        app: The Flask application instance.
    """

    @app.after_request
    def add_security_headers(response: Response) -> Response:
        """Inject security headers into every outgoing response."""
        return _apply_security_headers(response)

    @app.before_request
    def validate_origin() -> Response | None:
        """Reject cross-origin POST requests that fail origin validation."""
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            if not _validate_api_origin(request):
                logger.warning(
                    "Origin validation failed",
                    extra={"origin": request.headers.get("Origin"), "host": request.host},
                )
                return Response("Forbidden", status=403)
        return None
