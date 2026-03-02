from __future__ import annotations

import logging
from dataclasses import dataclass, field

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def _build_session(retries: int, backoff_factor: float) -> requests.Session:
    """Return a requests.Session with automatic retry + exponential backoff."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@dataclass
class GitHubClient:
    base_url: str
    token: str | None = None
    timeout: int = 20
    retries: int = 3
    backoff_factor: float = 0.5
    _session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._session = _build_session(self.retries, self.backoff_factor)

    def validate_token(self) -> bool:
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
            logger.error(f"Error validating GitHub token: {e}")
            return False

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def latest_release_tag(self, repo: str) -> str | None:
        url = f"{self.base_url}/repos/{repo}/releases/latest"
        try:
            response = self._session.get(url, headers=self._headers(), timeout=self.timeout)
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(f"GitHub: unauthorized access to {repo} (401)")
                return None
            if response.status_code == 403:
                logger.warning(f"GitHub: access denied to {repo} (403)")
                return None
            response.raise_for_status()
            data = response.json()
            return data.get("tag_name")
        except requests.RequestException as e:
            logger.warning(f"Error fetching release tag for {repo}: {e}")
            return None

    def latest_tag(self, repo: str) -> str | None:
        url = f"{self.base_url}/repos/{repo}/tags"
        try:
            response = self._session.get(url, headers=self._headers(), timeout=self.timeout)
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(f"GitHub: unauthorized access to {repo} (401)")
                return None
            if response.status_code == 403:
                logger.warning(f"GitHub: access denied to {repo} (403)")
                return None
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return data[0].get("name")
        except requests.RequestException as e:
            logger.warning(f"Error fetching tags for {repo}: {e}")
            return None

    def latest_ref(self, repo: str) -> str | None:
        tag = self.latest_release_tag(repo)
        if tag:
            return tag
        return self.latest_tag(repo)
