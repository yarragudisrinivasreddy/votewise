"""Structured logging configuration for VoteWise.

Configures Python's logging framework to emit JSON-structured log
records compatible with Google Cloud Logging's structured log format.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON formatter compatible with Google Cloud Logging structured logs.

    Emits each log record as a single-line JSON object containing
    ``severity``, ``message``, and any extra contextual fields attached
    to the log record via ``extra={}``.
    """

    _SEVERITY_MAP: dict[int, str] = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Serialise a log record to a JSON string.

        Args:
            record: The :class:`logging.LogRecord` to format.

        Returns:
            A JSON-encoded string suitable for Cloud Logging ingestion.
        """
        payload: dict[str, Any] = {
            "severity": self._SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Attach any extra fields added via extra={} on the logger call.
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with structured JSON output.

    Safe to call multiple times — subsequent calls are no-ops because
    the root logger's handlers are replaced, not appended.

    Args:
        level: The minimum log level to emit. Defaults to ``INFO``.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Suppress noisy third-party loggers.
    for noisy in ("werkzeug", "urllib3", "google.auth"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
