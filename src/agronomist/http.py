"""Shared HTTP utilities for Agronomist API clients.

Provides a pre-configured ``requests.Session`` with automatic
retry and exponential backoff, used by both the GitHub and
GitLab clients.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> requests.Session:
    """Return a ``requests.Session`` with retry and backoff.

    The session automatically retries on transient HTTP errors
    (429, 500, 502, 503, 504) using exponential backoff.

    Parameters:
        retries: Maximum number of retry attempts per request.
        backoff_factor: Multiplier applied between retries
            (e.g. 0.5 produces delays of 0.5 s, 1 s, 2 s, ...).

    Returns:
        A ``requests.Session`` configured with retry adapters
        for both ``http://`` and ``https://`` schemes.
    """
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
