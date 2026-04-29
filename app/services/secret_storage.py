"""Google Cloud Secret Manager and Cloud Storage services for VoteWise.

Secret Manager is used to retrieve runtime secrets securely.
Cloud Storage is used to archive session logs for audit purposes.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from google.cloud import secretmanager, storage

from app.exceptions import ServiceUnavailableError, StorageError
from app.models import ServiceHealth

logger = logging.getLogger(__name__)


class SecretManagerService:
    """Retrieves secrets from Google Cloud Secret Manager.

    Args:
        project_id: Google Cloud project identifier.
    """

    def __init__(self, project_id: str) -> None:
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """Access the latest version of a secret.

        Args:
            secret_id: The Secret Manager secret identifier.
            version: The secret version to access (default: ``'latest'``).

        Returns:
            The secret payload as a UTF-8 decoded string.

        Raises:
            ServiceUnavailableError: If the Secret Manager API call fails.
        """
        name = (
            f"projects/{self._project_id}/secrets/{secret_id}/versions/{version}"
        )
        try:
            response = self._client.access_secret_version(name=name)
            return response.payload.data.decode("utf-8")
        except Exception as exc:
            raise ServiceUnavailableError("secret_manager", str(exc)) from exc

    def health(self) -> ServiceHealth:
        """Probe Secret Manager with a list operation.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            parent = f"projects/{self._project_id}"
            next(iter(self._client.list_secrets(parent=parent)), None)
            return ServiceHealth(name="secret_manager", healthy=True)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return ServiceHealth(
                name="secret_manager", healthy=False, detail=str(exc)
            )


class CloudStorageService:
    """Archives session interaction logs to Google Cloud Storage.

    Args:
        project_id: Google Cloud project identifier.
        bucket_name: The Cloud Storage bucket to write logs into.
    """

    def __init__(self, project_id: str, bucket_name: str) -> None:
        self._client = storage.Client(project=project_id)
        self._bucket_name = bucket_name

    def archive_session(self, session_id: str, data: dict) -> None:
        """Write a JSON session log to Cloud Storage.

        The object is stored under a date-partitioned path:
        ``sessions/YYYY/MM/DD/{session_id}.json``.

        Args:
            session_id: The anonymised session identifier.
            data: A serialisable dictionary of session data.

        Raises:
            StorageError: If the upload fails.
        """
        now = datetime.now(tz=timezone.utc)
        path = f"sessions/{now:%Y/%m/%d}/{session_id}.json"
        try:
            bucket = self._client.bucket(self._bucket_name)
            blob = bucket.blob(path)
            blob.upload_from_string(
                json.dumps(data, ensure_ascii=False),
                content_type="application/json",
            )
            logger.info("Session archived", extra={"path": path})
        except Exception as exc:
            raise StorageError("archive", str(exc)) from exc

    def health(self) -> ServiceHealth:
        """Probe Cloud Storage by checking bucket existence.

        Returns:
            A :class:`~app.models.ServiceHealth` snapshot.
        """
        try:
            self._client.bucket(self._bucket_name).exists()
            return ServiceHealth(name="storage", healthy=True)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return ServiceHealth(name="storage", healthy=False, detail=str(exc))
