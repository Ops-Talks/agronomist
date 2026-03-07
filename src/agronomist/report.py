"""JSON report builder and writer for Agronomist."""

from __future__ import annotations

import json
from datetime import datetime, timezone


def build_report(
    root: str,
    updates: list[dict[str, object]],
) -> dict[str, object]:
    """Build an in-memory report dict from a list of updates.

    Parameters:
        root: The root directory that was scanned.
        updates: List of update dicts produced by the CLI.

    Returns:
        A dict containing ``generated_at`` (ISO 8601 UTC),
        ``root``, and ``updates``.
    """
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": root,
        "updates": updates,
    }


def write_report(
    path: str,
    report: dict[str, object],
) -> None:
    """Serialize a report dict to a JSON file.

    The output is pretty-printed with sorted keys and a
    trailing newline.

    Parameters:
        path: Destination file path.
        report: The report dict to write.
    """
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
