import json
import os


def load_state(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_state(path: str, rows: list[dict]) -> None:
    with open(path, "w") as f:
        json.dump(rows, f, indent=2)


def diff(
    old_rows: list[dict],
    new_rows: list[dict],
    monitored_cols: list[str],
) -> list[dict]:
    """Compare old and new snapshots by row position.

    Returns a list of change records for rows where a monitored column value
    changed. Each record contains the current row data plus old/new values for
    the columns that changed.
    """
    if not old_rows:
        # First run — treat as baseline with no changes
        return []

    changes = []
    for idx, new_row in enumerate(new_rows):
        if idx >= len(old_rows):
            # New row added since last run — not a value change, skip
            continue

        old_row = old_rows[idx]
        changed_cols = {}
        for col in monitored_cols:
            old_val = old_row.get(col, "")
            new_val = new_row.get(col, "")
            if old_val != new_val:
                changed_cols[col] = {"old": old_val, "new": new_val}

        if changed_cols:
            changes.append(
                {
                    "row_index": idx,
                    "row": new_row,
                    "changes": changed_cols,
                }
            )

    return changes
