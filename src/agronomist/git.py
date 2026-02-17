from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitClient:
    timeout: int = 20

    def latest_ref(self, repo_url: str) -> str | None:
        cmd = [
            "git",
            "ls-remote",
            "--tags",
            "--sort=-v:refname",
            repo_url,
        ]
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Git ls-remote for {repo_url} timed out")
            return None
        except subprocess.CalledProcessError as e:
            if "not found" in e.stderr or "fatal:" in e.stderr:
                logger.warning(f"Git: repository {repo_url} not found or no access")
            else:
                logger.warning(f"Git ls-remote failed for {repo_url}: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("Git not installed or not in PATH")
            return None
        except Exception as e:
            logger.error(f"Unexpected error running git ls-remote: {e}")
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
