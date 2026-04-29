"""Health check and index route Blueprint for VoteWise.

Provides liveness and readiness endpoints suitable for Cloud Run
health probes, plus the root route that serves the SPA.
"""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, render_template

health_bp = Blueprint("health", __name__)
logger = logging.getLogger(__name__)


@health_bp.route("/", methods=["GET"])
def index():
    """Serve the VoteWise single-page application.

    Returns:
        Rendered ``index.html`` template.
    """
    return render_template("index.html")


@health_bp.route("/health", methods=["GET"])
def health():
    """Aggregate health check across all Google Cloud service dependencies.

    Probes each registered service and returns a JSON summary with an
    overall ``healthy`` flag. Cloud Run uses this endpoint for readiness
    checks; the response is always HTTP 200 to avoid restart loops —
    individual service failures are surfaced in the ``services`` array.

    Returns:
        JSON object with keys:
          - ``healthy`` (bool): True if all services report healthy.
          - ``services`` (list): Per-service health snapshots.
    """
    services = []
    for key in ("GEMINI", "TRANSLATE", "FIRESTORE", "SECRET_MANAGER", "STORAGE"):
        svc = current_app.config.get(key)
        if svc is not None:
            health_result = svc.health()
            services.append(health_result.to_dict())

    overall = all(s["healthy"] for s in services)

    logger.info(
        "Health check completed",
        extra={"healthy": overall, "service_count": len(services)},
    )
    return jsonify({"healthy": overall, "services": services}), 200
