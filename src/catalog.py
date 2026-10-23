import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SAMPLE_FILES = [
    "crazing_1.jpg", "crazing_2.jpg", "crazing_3.jpg", "crazing_4.jpg", "crazing_5.jpg",
    "patches_1.jpg", "patches_2.jpg", "patches_3.jpg", "patches_4.jpg", "patches_5.jpg",
    "inclusion_1.jpg", "inclusion_2.jpg", "inclusion_3.jpg", "inclusion_4.jpg",
    "pitted_surface_1.jpg", "pitted_surface_2.jpg", "pitted_surface_3.jpg",
    "pitted_surface_4.jpg", "pitted_surface_5.jpg",
    "rolled-in_scale_1.jpg", "rolled-in_scale_2.jpg", "rolled-in_scale_3.jpg",
    "rolled-in_scale_4.jpg", "rolled-in_scale_5.jpg",
    "scratches_1.jpg", "scratches_2.jpg", "scratches_3.jpg", "scratches_4.jpg", "scratches_5.jpg",
]

PREFIX_TO_CLASS = {
    "crazing": "Crazing",
    "patches": "Patches",
    "inclusion": "Inclusion",
    "pitted_surface": "Pitted surface",
    "rolled-in_scale": "Rolled-in scale",
    "scratches": "Scratches",
}

_NAME_RE = re.compile(r"^(.+)_\d+\.jpg$")

with open(ROOT / "config" / "class_mapping.json") as _f:
    _known = set(json.load(_f).values())
if not set(PREFIX_TO_CLASS.values()) <= _known:
    raise RuntimeError("catalog classes not in class_mapping.json")


def expected_class(file_name: str) -> str:
    m = _NAME_RE.match(file_name)
    if not m or m.group(1) not in PREFIX_TO_CLASS:
        raise ValueError("unknown sample name")
    return PREFIX_TO_CLASS[m.group(1)]


def sample_path(file_name: str) -> Path:
    if file_name not in SAMPLE_FILES:
        raise ValueError("unknown sample name")
    return ROOT / "data" / file_name
