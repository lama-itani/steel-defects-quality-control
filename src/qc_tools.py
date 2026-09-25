import json
import re
from pathlib import Path

from src.inspection import inspect_image as run_inspection

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "outputs" / "inspections"

SAMPLES = {
    "scratches_86.jpg": "data/scratches_86.jpg",
    "patches_274.jpg": "data/patches_274.jpg",
}

CLASSES = frozenset(
    json.loads(
        (ROOT / "config/class_mapping.json").read_text(encoding="utf-8")
    ).values()
)


def inspect_image(image_id: str) -> dict:
    """Inspect an allowlisted sample and persist its result."""
    if not isinstance(image_id, str) or image_id not in SAMPLES:
        raise ValueError("Unknown sample ID")

    sample = (ROOT / SAMPLES[image_id]).resolve()
    if not sample.is_relative_to((ROOT / "data").resolve()):
        raise ValueError("Sample path is outside the data directory")
    if not sample.is_file():
        raise FileNotFoundError("Allowlisted sample is unavailable")

    return run_inspection(str(sample))


def get_inspection(inspection_id: str) -> dict:
    """Retrieve a completed inspection using its unique ID."""
    if (
        not isinstance(inspection_id, str)
        or re.fullmatch(r"[0-9a-f]{32}", inspection_id) is None
    ):
        raise ValueError("Invalid inspection ID")

    result_path = (STORE / inspection_id / "result.json").resolve()
    if not result_path.is_relative_to(STORE.resolve()):
        raise ValueError("Invalid inspection location")
    if not result_path.is_file():
        raise FileNotFoundError("Inspection not found")

    result = json.loads(result_path.read_text(encoding="utf-8"))
    if (
        not isinstance(result, dict)
        or result.get("inspection_id") != inspection_id
        or result.get("status") != "completed"
    ):
        raise ValueError("Invalid saved inspection")

    return result


def lookup_defect_guidance(defect_class: str) -> dict:
    """Report guidance availability for a supported defect class."""
    if not isinstance(defect_class, str) or defect_class not in CLASSES:
        raise ValueError("Unknown defect class")

    # No reviewed guidance has been supplied.
    return {
        "defect_class": defect_class,
        "status": "guidance unavailable",
        "guidance": None,
        "source": None,
        "version": None,
    }