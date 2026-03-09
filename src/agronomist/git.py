"""Git CLI resolver for determining the latest tag.

Shells out to ``git ls-remote --tags`` and parses the output
to find the most recent version-sorted tag.
"""

from __future__ import annotations

import subprocess  # nosec B404, B603
from dataclasses import dataclass

from .exceptions import ResolverError


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
            or None when no tags exist.

        Raises:
            ResolverError: When the git command fails due to
                timeout, missing binary, or process error.
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
        except subprocess.TimeoutExpired as exc:
            raise ResolverError(
                f"Git ls-remote for {repo_url} timed out"
            ) from exc
        except subprocess.CalledProcessError as exc:
            if "not found" in exc.stderr or "fatal:" in exc.stderr:
                raise ResolverError(
                    f"Git: repository {repo_url} not found"
                    " or no access"
                ) from exc
            raise ResolverError(
                f"Git ls-remote failed for {repo_url}:"
                f" {exc.stderr}"
            ) from exc
        except FileNotFoundError as exc:
            raise ResolverError(
                "Git not installed or not in PATH"
            ) from exc
        except Exception as exc:
            raise ResolverError(
                "Unexpected error running git ls-remote:"
                f" {exc}"
            ) from exc

        for line in result.stdout.splitlines():
            try:
                _, ref = line.split("\t", 1)
            except ValueError:
                continue
            ref = ref.strip()
            if ref.endswith("^{}"):
                continue
            if ref.startswith("refs/tags/"):
                return ref.replace("refs/tags/", "", 1)
        return None
