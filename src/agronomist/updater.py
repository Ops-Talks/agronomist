from __future__ import annotations


def apply_updates(root: str, updates: list[dict[str, object]]) -> list[str]:
    touched: list[str] = []

    updates_by_file: dict[str, list[dict[str, object]]] = {}
    for update in updates:
        for file_path in update["files"]:
            updates_by_file.setdefault(file_path, []).append(update)

    for file_path, file_updates in updates_by_file.items():
        full_path = f"{root}/{file_path}"
        try:
            with open(full_path, encoding="utf-8", newline="") as handle:
                content = handle.read()
        except OSError:
            continue

        new_content = content
        for update in file_updates:
            for replacement in update["replacements"]:
                new_content = new_content.replace(replacement["from"], replacement["to"], 1)

        if new_content != content:
            with open(full_path, "w", encoding="utf-8", newline="") as handle:
                handle.write(new_content)
            touched.append(file_path)

    return touched
