from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitClient:
    timeout: int = 20

    def latest_ref(self, repo_url: str) -> Optional[str]:
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
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

        for line in result.stdout.splitlines():
            _, ref = line.split("\t", 1)
            if ref.endswith("^{}"):
                continue
            if ref.startswith("refs/tags/"):
                return ref.replace("refs/tags/", "", 1)
        return None
