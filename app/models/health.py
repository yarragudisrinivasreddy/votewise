"""Service health model for VoteWise.

Represents the health status of a single Google Cloud service
dependency, used by the ``/health`` endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["ServiceHealth"]


@dataclass
class ServiceHealth:
    """Health status of a single external service dependency.

    Attributes:
        name: Service name (e.g. 'firestore', 'translate').
        healthy: Whether the service is reachable and functional.
        detail: Optional additional context (e.g. error message).
    """

    name: str
    healthy: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary.

        Returns:
            Dictionary with ``name``, ``healthy``, and ``detail``.
        """
        return {"name": self.name, "healthy": self.healthy, "detail": self.detail}
