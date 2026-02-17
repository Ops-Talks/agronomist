from __future__ import annotations

import json
from datetime import datetime, timezone


def build_report(
    root: str,
    updates: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": root,
        "updates": updates,
    }


def write_report(path: str, report: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
