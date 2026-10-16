import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SAMPLE_FILES = [
    "crazing_151.jpg", "crazing_153.jpg", "crazing_166.jpg",
    "crazing_240.jpg", "crazing_241.jpg",
    "patches_28.jpg", "patches_63.jpg", "patches_128.jpg",
    "patches_151.jpg", "patches_274.jpg",
    "inclusion_161.jpg", "inclusion_169.jpg",
    "inclusion_195.jpg", "inclusion_263.jpg",
    "pitted_surface_18.jpg", "pitted_surface_64.jpg",
    "pitted_surface_110.jpg", "pitted_surface_125.jpg",
    "pitted_surface_175.jpg",
    "rolled-in_scale_14.jpg", "rolled-in_scale_80.jpg",
    "rolled-in_scale_138.jpg", "rolled-in_scale_176.jpg",
    "rolled-in_scale_216.jpg",
    "scratches_86.jpg", "scratches_195.jpg", "scratches_264.jpg",
    "scratches_286.jpg", "scratches_300.jpg",
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
