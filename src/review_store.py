import json
import os
import re
from datetime import datetime, timezone

import numpy as np

from src import qc_tools
from src.catalog import SAMPLE_FILES

STORE = qc_tools.STORE
VERDICTS = {"agree", "disagree", "unsure"}
MAX_NOTE = 2000


def _check_id(inspection_id):
    if (
        not isinstance(inspection_id, str)
        or re.fullmatch(r"[0-9a-f]{32}", inspection_id) is None
    ):
        raise ValueError("Invalid inspection ID")


def load_masks(inspection_id: str):
    """Return saved masks (6, H, W), or None for older inspections."""
    _check_id(inspection_id)
    path = (STORE / inspection_id / "masks.npz").resolve()
    if not path.is_relative_to(STORE.resolve()):
        raise ValueError("Invalid inspection location")
    if not path.is_file():
        return None

    with np.load(path) as data:
        masks = data["masks"]
    if masks.ndim != 3 or masks.shape[0] != 6:
        raise ValueError("Invalid saved masks")
    return masks


def latest_inspections() -> dict:
    """Newest valid inspection per catalog image."""
    latest = {}
    if not STORE.is_dir():
        return latest
    for folder in STORE.iterdir():
        try:
            result = qc_tools.get_inspection(folder.name)
        except (ValueError, OSError):
            continue
        name = result.get("image_id")
        if name not in SAMPLE_FILES:
            continue
        created = result.get("created_at", "")
        if name not in latest or created > latest[name].get("created_at", ""):
            latest[name] = result
    return latest


def append_review(inspection_id: str, verdict: str, note: str) -> dict:
    if verdict not in VERDICTS:
        raise ValueError("Invalid verdict")
    note = (note or "").strip()
    if len(note) > MAX_NOTE:
        raise ValueError("Note is too long")
    if verdict == "disagree" and not note:
        raise ValueError("A note is required for Disagree")
    qc_tools.get_inspection(inspection_id)

    record = {
        "verdict": verdict,
        "note": note,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    path = STORE / inspection_id / "reviews.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return record


def review_history(inspection_id: str) -> list:
    """Reviews for an inspection, newest first."""
    _check_id(inspection_id)
    path = STORE / inspection_id / "reviews.jsonl"
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict) and rec.get("verdict") in VERDICTS:
            records.append(rec)
    return records[::-1]


def latest_review(inspection_id: str):
    history = review_history(inspection_id)
    return history[0] if history else None
