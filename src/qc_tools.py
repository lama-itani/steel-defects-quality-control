import json
import re
from pathlib import Path

from src.catalog import SAMPLE_FILES
from src.inspection import inspect_image as run_inspection

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "outputs" / "inspections"

SAMPLES = {name: f"data/{name}" for name in SAMPLE_FILES}

CLASSES = frozenset(
    json.loads(
        (ROOT / "config/class_mapping.json").read_text(encoding="utf-8")
    ).values()
)

GUIDANCE_PATH = ROOT / "config/defect_guidance.json"
GUIDANCE_STATUSES = frozenset(
    {"approved", "draft_pending_review", "guidance unavailable"}
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


def _load_guidance(path=GUIDANCE_PATH, classes=CLASSES):
    """Return the validated guidance document, or None if unusable."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Guidance must be an object")
        document = data["document"]
        sources = data["sources"]
        common = data["common_handling"]
        entries = data["classes"]
        if not (
            isinstance(document, dict)
            and isinstance(sources, dict)
            and isinstance(common, dict)
            and isinstance(common.get("steps"), list)
            and isinstance(entries, dict)
        ):
            raise ValueError("Malformed guidance structure")
        if set(entries) != set(classes):
            raise ValueError("Guidance classes do not match the class mapping")

        for name, entry in entries.items():
            if (
                not isinstance(entry, dict)
                or entry.get("status") not in GUIDANCE_STATUSES
            ):
                raise ValueError("Invalid class entry")
            for reference in entry.get("sources", []):
                if _source_id(reference) not in sources:
                    raise ValueError("Unknown source ID")
        for reference in common.get("sources", []):
            if _source_id(reference) not in sources:
                raise ValueError("Unknown source ID")
        return data
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def _source_id(reference):
    if not isinstance(reference, str) or not reference.split():
        raise ValueError("Invalid source reference")
    return reference.split()[0]


GUIDANCE = _load_guidance()


def _unavailable(defect_class):
    return {
        "defect_class": defect_class,
        "status": "guidance unavailable",
        "guidance": None,
        "source": None,
        "version": None,
    }


def lookup_defect_guidance(defect_class: str) -> dict:
    """Return guidance for a supported defect class, if it may be shown."""
    if not isinstance(defect_class, str) or defect_class not in CLASSES:
        raise ValueError("Unknown defect class")

    if GUIDANCE is None:
        return _unavailable(defect_class)

    entry = GUIDANCE["classes"][defect_class]
    status = entry["status"]
    if status not in ("approved", "draft_pending_review"):
        return _unavailable(defect_class)

    sources = []
    for reference in entry.get("sources", []):
        source_id, _, section = reference.partition(" ")
        source = GUIDANCE["sources"][source_id]
        sources.append({
            "citation": source.get("citation"),
            "section": section.strip() or None,
            "url": source.get("url"),
            "access": source.get("access"),
        })

    return {
        "defect_class": defect_class,
        "status": status,
        "guidance": {
            "definition": entry.get("definition"),
            "typical_causes": entry.get("typical_causes", []),
            "common_handling": GUIDANCE["common_handling"]["steps"],
            "class_specific_handling": entry.get(
                "class_specific_handling", []
            ),
        },
        "source": sources,
        "version": GUIDANCE["document"].get("version"),
    }