"""Bitbucket Cloud API client for resolving module versions.

Uses the Bitbucket Cloud REST API (v2.0) to query the latest
tag for a given repository identified by its workspace and
repository slug.

Authentication supports two modes:

* **App Password** (HTTP Basic): when both a ``username`` and
  ``token`` are configured.
* **Access Token** (Bearer): when only a ``token`` is configured
  (e.g. Repository or Workspace Access Tokens).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests

from .exceptions import AuthenticationError, NetworkError
from .http import build_session

logger = logging.getLogger(__name__)


@dataclass
class BitbucketClient:
    """Client that resolves the latest version via Bitbucket API.

    Attributes:
        base_url: Bitbucket Cloud API base URL.
        token: Optional App Password or Access Token.
        username: Optional Bitbucket username for App Password
            HTTP Basic authentication.
        timeout: HTTP request timeout in seconds.
        retries: Number of automatic retries on transient errors.
        backoff_factor: Exponential backoff multiplier.
    """

    base_url: str = "https://api.bitbucket.org/2.0"
    token: str | None = None
    username: str | None = None
    timeout: int = 20
    retries: int = 3
    backoff_factor: float = 0.5
    _session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the HTTP session with retry settings."""
        self._session = build_session(self.retries, self.backoff_factor)

    @staticmethod
    def detect_bitbucket_host(repo_url: str) -> str | None:
        """Detect whether a URL points to Bitbucket Cloud.

        Parameters:
            repo_url: Full repository URL to inspect.

        Returns:
            ``"https://bitbucket.org"`` when the URL netloc
            contains ``bitbucket.org``, None otherwise.
        """
        try:
            parsed = urlparse(repo_url)
            if "bitbucket.org" in parsed.netloc:
                return "https://bitbucket.org"
        except Exception:  # nosec B110
            logger.debug(
                "Failed to parse URL for Bitbucket detection: %s",
                repo_url,
            )
        return None

    def _auth(self) -> tuple[str, str] | None:
        """Build HTTP Basic auth credentials when available.

        Returns:
            A ``(username, token)`` tuple when both fields are
            configured, otherwise None.
        """
        if self.username and self.token:
            return (self.username, self.token)
        return None

    def _headers(self) -> dict[str, str]:
        """Build default request headers.

        Returns:
            A dict containing the ``Accept`` header and, when a
            bearer-only token is configured (no username), an
            ``Authorization: Bearer ...`` header.
        """
        headers: dict[str, str] = {"Accept": "application/json"}
        if self.token and not self.username:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def validate_token(self) -> bool:
        """Verify that the configured token is valid.

        Uses HTTP Basic auth when both ``username`` and ``token``
        are set (App Password), otherwise Bearer authentication.

        Returns:
            True if the token is valid or no token is set.

        Raises:
            AuthenticationError: When the API rejects the
                token (401/403) or a network error occurs.
        """
        if not self.token:
            return True
        url = f"{self.base_url}/user"
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                auth=self._auth(),
                timeout=self.timeout,
            )
            if response.status_code == 401:
                raise AuthenticationError("Bitbucket token invalid or expired")
            if response.status_code == 403:
                raise AuthenticationError("Bitbucket token insufficient permissions")
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            raise AuthenticationError(f"Error validating Bitbucket token: {exc}") from exc

    def latest_tag(self, workspace: str, repo_slug: str) -> str | None:
        """Fetch the most recent tag for a Bitbucket repository.

        Parameters:
            workspace: Bitbucket workspace (user or team).
            repo_slug: Repository slug within the workspace.

        Returns:
            The tag name string, or None on any error.

        Raises:
            NetworkError: When a request exception occurs.
        """
        url = f"{self.base_url}/repositories/{workspace}/{repo_slug}/refs/tags"
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                auth=self._auth(),
                timeout=self.timeout,
                params={
                    "sort": "-target.date",
                    "pagelen": 1,
                },  # type: ignore[arg-type]
            )
            if response.status_code == 404:
                logger.warning(
                    "Bitbucket: repository not found %s/%s (404)",
                    workspace,
                    repo_slug,
                )
                return None
            if response.status_code == 401:
                logger.warning(
                    "Bitbucket: unauthorized access to %s/%s (401)",
                    workspace,
                    repo_slug,
                )
                return None
            if response.status_code == 403:
                logger.warning(
                    "Bitbucket: access denied to %s/%s (403)",
                    workspace,
                    repo_slug,
                )
                return None
            response.raise_for_status()
            data = response.json()
            values = data.get("values") or []
            if not values:
                return None
            return str(values[0].get("name"))
        except requests.RequestException as exc:
            raise NetworkError(
                f"Error fetching Bitbucket tags for {workspace}/{repo_slug}: {exc}"
            ) from exc

    def latest_ref(self, repo_url: str) -> str | None:
        """Return the latest tag for a Bitbucket repository URL.

        Extracts the ``workspace`` and ``repo_slug`` from the URL
        path and delegates to :meth:`latest_tag`.

        Parameters:
            repo_url: Full HTTPS URL to the Bitbucket repository.

        Returns:
            The tag name string, or None if unavailable.
        """
        try:
            parsed = urlparse(repo_url)
            path = parsed.path.strip("/")
            if path.endswith(".git"):
                path = path[:-4]
            segments = path.split("/")
            if len(segments) < 2 or not segments[0] or not segments[1]:
                logger.error(
                    "Bitbucket: invalid repository URL (need workspace/repo): %s",
                    repo_url,
                )
                return None
            workspace, repo_slug = segments[0], segments[1]
            return self.latest_tag(workspace, repo_slug)
        except Exception as exc:
            logger.error("Error processing repo_url for Bitbucket: %s", exc)
            return None
