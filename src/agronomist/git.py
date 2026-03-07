"""Git CLI resolver for determining the latest tag.

Shells out to ``git ls-remote --tags`` and parses the output
to find the most recent version-sorted tag.
"""

from __future__ import annotations

import logging
import subprocess  # nosec: B404, B603
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitClient:
    """Resolver that uses the local ``git`` binary.

    Attributes:
        timeout: Maximum seconds to wait for ``git ls-remote``.
    """

    timeout: int = 20

    def latest_ref(self, repo_url: str) -> str | None:
        """Return the latest tag from a remote repository.

        Runs ``git ls-remote --tags --sort=-v:refname`` and
        returns the first non-peeled tag (skips ``^{}`` lines).

        Parameters:
            repo_url: Full URL of the remote Git repository.

        Returns:
            The tag name (without ``refs/tags/`` prefix),
            or None when no tags exist or on any error.
        """
        cmd = [
            "git",
            "ls-remote",
            "--tags",
            "--sort=-v:refname",
            repo_url,
        ]
        try:
            result = subprocess.run(  # nosec B603
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            logger.error("Git ls-remote for %s timed out", repo_url)
            return None
        except subprocess.CalledProcessError as e:
            if "not found" in e.stderr or "fatal:" in e.stderr:
                logger.warning(
                    "Git: repository %s not found or no access",
                    repo_url,
                )
            else:
                logger.warning(
                    "Git ls-remote failed for %s: %s",
                    repo_url,
                    e.stderr,
                )
            return None
        except FileNotFoundError:
            logger.error("Git not installed or not in PATH")
            return None
        except Exception as e:
            logger.error("Unexpected error running git ls-remote: %s", e)
            return None

        for line in result.stdout.splitlines():
            try:
                _, ref = line.split("\t", 1)
            except ValueError:
                continue
            if ref.endswith("^{}"):
                continue
            if ref.startswith("refs/tags/"):
                return ref.replace("refs/tags/", "", 1)
        return None
