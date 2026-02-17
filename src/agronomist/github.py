from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class GitHubClient:
    base_url: str
    token: Optional[str] = None

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def latest_release_tag(self, repo: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{repo}/releases/latest"
        response = requests.get(url, headers=self._headers(), timeout=20)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name")

    def latest_tag(self, repo: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{repo}/tags"
        response = requests.get(url, headers=self._headers(), timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        return data[0].get("name")

    def latest_ref(self, repo: str) -> Optional[str]:
        tag = self.latest_release_tag(repo)
        if tag:
            return tag
        return self.latest_tag(repo)
