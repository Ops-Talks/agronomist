from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

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
class GitLabClient:
    base_url: str
    token: str | None = None
    timeout: int = 20
    retries: int = 3
    backoff_factor: float = 0.5
    _session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._session = _build_session(self.retries, self.backoff_factor)

    @staticmethod
    def detect_gitlab_host(repo_url: str) -> str | None:
        try:
            parsed = urlparse(repo_url)
            if "gitlab" in parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:  # nosec B110
            pass
        return None

    def validate_token(self) -> bool:
        if not self.token:
            return True
        url = f"{self.base_url}/api/v4/user"
        headers = {"PRIVATE-TOKEN": self.token}
        try:
            response = self._session.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 401:
                logger.error("GitLab token invalid or expired")
                return False
            if response.status_code == 403:
                logger.error("GitLab token insufficient permissions")
                return False
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Error validating GitLab token: {e}")
            return False

    def _headers(self) -> dict:
        headers = {}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def latest_tag(self, project_id: str) -> str | None:
        url = f"{self.base_url}/api/v4/projects/{project_id}/repository/tags"
        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
                params={"per_page": 1, "sort": "updated_desc"},  # type: ignore[arg-type]
            )
            if response.status_code == 404:
                return None
            if response.status_code == 401:
                logger.warning(f"GitLab: unauthorized access to {project_id} (401)")
                return None
            if response.status_code == 403:
                logger.warning(f"GitLab: access denied to {project_id} (403)")
                return None
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return data[0].get("name")
        except requests.RequestException as e:
            logger.warning(f"Error fetching GitLab tags for {project_id}: {e}")
            return None

    def latest_ref(self, repo_url: str) -> str | None:
        try:
            parsed = urlparse(repo_url)
            path = parsed.path.strip("/")
            if path.endswith(".git"):
                path = path[:-4]
            project_id = path.replace("/", "%2F")
            return self.latest_tag(project_id)
        except Exception as e:
            logger.error(f"Error processing repo_url for GitLab: {e}")
            return None
