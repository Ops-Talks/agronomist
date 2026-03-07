"""GitHub API client for resolving module versions.

Uses the GitHub REST API to query the latest release or tag
for a given repository. Falls back from releases to tags when
no published release exists.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests

from .http import build_session

logger = logging.getLogger(__name__)


@dataclass
class GitHubClient:
    """Client that resolves the latest version via GitHub API.

    Attributes:
        base_url: GitHub API base URL (supports Enterprise).
        token: Optional Bearer token for authentication.
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

    def validate_token(self) -> bool:
        """Verify that the configured token is valid.

        Returns:
            True if the token is valid or no token is set,
            False if the API rejects the token.
        """
        if not self.token:
            return True
        url = f"{self.base_url}/user"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 401:
                logger.error("GitHub token invalid or expired")
                return False
            if response.status_code == 403:
                logger.error("GitHub token insufficient permissions")
                return False
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error validating GitHub token: %s", e)
            return False

    def _headers(self) -> dict[str, str]:
        """Build default request headers.

        Returns:
            A dict containing the Accept header and, when a
            token is configured, the Authorization header.
        """
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def latest_release_tag(self, repo: str) -> str | None:
        """Fetch the tag name of the latest published release.

        Parameters:
            repo: Repository in ``owner/name`` format.

        Returns:
            The ``tag_name`` string, or None on any error.
        """
        url = f"{self.base_url}/repos/{repo}/releases/latest"
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(
                    "GitHub: unauthorized access to %s (401)",
                    repo,
                )
                return None
            if response.status_code == 403:
                logger.warning("GitHub: access denied to %s (403)", repo)
                return None
            response.raise_for_status()
            data = response.json()
            return str(data.get("tag_name"))
        except requests.RequestException as e:
            logger.warning(
                "Error fetching release tag for %s: %s",
                repo,
                e,
            )
            return None

    def latest_tag(self, repo: str) -> str | None:
        """Fetch the name of the most recent tag.

        Parameters:
            repo: Repository in ``owner/name`` format.

        Returns:
            The tag name string, or None on any error.
        """
        url = f"{self.base_url}/repos/{repo}/tags"
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(
                    "GitHub: unauthorized access to %s (401)",
                    repo,
                )
                return None
            if response.status_code == 403:
                logger.warning("GitHub: access denied to %s (403)", repo)
                return None
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return str(data[0].get("name"))
        except requests.RequestException as e:
            logger.warning("Error fetching tags for %s: %s", repo, e)
            return None

    def latest_ref(self, repo: str) -> str | None:
        """Return the latest version ref for a repository.

        Prefers the latest GitHub Release tag. If none exists,
        falls back to the most recent Git tag.

        Parameters:
            repo: Repository in ``owner/name`` format.

        Returns:
            The tag name string, or None if unavailable.
        """
        tag = self.latest_release_tag(repo)
        if tag:
            return tag
        return self.latest_tag(repo)
