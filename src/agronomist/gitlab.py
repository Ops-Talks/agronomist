"""GitLab API client for resolving module versions.

Uses the GitLab REST API (v4) to query the latest tag for a
given project, identified by its URL-encoded path.
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
class GitLabClient:
    """Client that resolves the latest version via GitLab API.

    Attributes:
        base_url: GitLab instance base URL.
        token: Optional ``PRIVATE-TOKEN`` for authentication.
        timeout: HTTP request timeout in seconds.
        retries: Number of automatic retries on transient errors.
        backoff_factor: Exponential backoff multiplier.
    """

    base_url: str
    token: str | None = None
    timeout: int = 20
    retries: int = 3
    backoff_factor: float = 0.5
    _session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the HTTP session with retry settings."""
        self._session = build_session(self.retries, self.backoff_factor)

    @staticmethod
    def detect_gitlab_host(repo_url: str) -> str | None:
        """Detect whether a URL points to a GitLab instance.

        Parameters:
            repo_url: Full repository URL to inspect.

        Returns:
            The scheme + host (e.g. ``https://gitlab.com``)
            when the netloc contains ``gitlab``, None otherwise.
        """
        try:
            parsed = urlparse(repo_url)
            if "gitlab" in parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:  # nosec B110
            logger.debug(
                "Failed to parse URL for GitLab detection: %s",
                repo_url,
            )
        return None

    def validate_token(self) -> bool:
        """Verify that the configured token is valid.

        Returns:
            True if the token is valid or no token is set.

        Raises:
            AuthenticationError: When the API rejects the
                token (401/403) or a network error occurs.
        """
        if not self.token:
            return True
        url = f"{self.base_url}/api/v4/user"
        headers = {"PRIVATE-TOKEN": self.token}
        try:
            response = self._session.get(
                url, headers=headers, timeout=self.timeout,
            )
            if response.status_code == 401:
                raise AuthenticationError(
                    "GitLab token invalid or expired"
                )
            if response.status_code == 403:
                raise AuthenticationError(
                    "GitLab token insufficient permissions"
                )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            raise AuthenticationError(
                f"Error validating GitLab token: {exc}"
            ) from exc

    def _headers(self) -> dict[str, str]:
        """Build default request headers.

        Returns:
            A dict containing the ``PRIVATE-TOKEN`` header when
            a token is configured, or an empty dict otherwise.
        """
        headers: dict[str, str] = {}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def latest_tag(
        self,
        project_id: str,
        base_url: str | None = None,
    ) -> str | None:
        """Fetch the most recent tag for a GitLab project.

        Parameters:
            project_id: URL-encoded project path
                (e.g. ``mygroup%2Fmyproject``).
            base_url: Override the instance base URL for
                this request (used for self-hosted GitLab).

        Returns:
            The tag name string, or None on any error.
        """
        effective_url = base_url or self.base_url
        url = (
            f"{effective_url}/api/v4/projects"
            f"/{project_id}/repository/tags"
        )
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
                params={
                    "per_page": 1,
                    "order_by": "updated",
                    "sort": "desc",
                },  # type: ignore[arg-type]
            )
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(
                    "GitLab: unauthorized access to %s (401)",
                    project_id,
                )
                return None
            if response.status_code == 403:
                logger.warning(
                    "GitLab: access denied to %s (403)",
                    project_id,
                )
                return None
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return str(data[0].get("name"))
        except requests.RequestException as exc:
            raise NetworkError(
                f"Error fetching GitLab tags for"
                f" {project_id}: {exc}"
            ) from exc

    def latest_ref(self, repo_url: str) -> str | None:
        """Return the latest tag for a repository URL.

        Extracts the project path from the URL, URL-encodes it,
        and delegates to :meth:`latest_tag`.

        Parameters:
            repo_url: Full HTTPS URL to the GitLab repository.

        Returns:
            The tag name string, or None if unavailable.
        """
        try:
            parsed = urlparse(repo_url)
            path = parsed.path.strip("/")
            if path.endswith(".git"):
                path = path[:-4]
            project_id = path.replace("/", "%2F")
            host_url = (
                f"{parsed.scheme}://{parsed.netloc}"
                if parsed.netloc
                else None
            )
            return self.latest_tag(
                project_id, base_url=host_url,
            )
        except Exception as e:
            logger.error("Error processing repo_url for GitLab: %s", e)
            return None
