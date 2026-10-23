# Imports
import json
from pathlib import Path
from time import perf_counter

from datetime import datetime, timezone
from uuid import uuid4

import cv2
import numpy as np

from src.inference import OnnxDefectModel
from src.preprocessing import preprocess_image
from src.postprocessing import postprocess_output
from src.visualization import create_defect_overlay


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "Unet.onnx"
DEPLOYMENT_NAME = "local-onnx"

_model = None


def _get_model() -> OnnxDefectModel:
    global _model
    if _model is None:
        _model = OnnxDefectModel(MODEL_PATH)
    return _model


def inspect_image(image_path: str) -> dict:
    """Inspect one image with the in-process ONNX model."""
    started = perf_counter()
    path = Path(image_path)
    if not path.is_absolute():
        path = ROOT / path

    tensor, original = preprocess_image(path)

    inference_started = perf_counter()
    logits = _get_model().predict(tensor)
    inference_ms = (perf_counter() - inference_started) * 1000

    if logits.shape != (1, 6, 128, 128):
        raise ValueError(f"Unexpected output shape: {logits.shape}")
    if not np.isfinite(logits).all():
        raise ValueError("Model returned non-finite values")

    masks, region_counts = postprocess_output(
        logits,
        original.shape[:2],
        threshold=0.5,
        min_size=200,
    )
    mapping = json.loads(
        (ROOT / "config/class_mapping.json").read_text()
    )
    overlay, detected_classes = create_defect_overlay(
        original, masks, mapping
    )

    inspection_id = uuid4().hex
    output_dir = ROOT / "outputs" / "inspections" / inspection_id
    output_dir.mkdir(parents=True, exist_ok=False)
    overlay_path = output_dir / "overlay.jpg"

    if not cv2.imwrite(str(overlay_path), overlay):
        raise RuntimeError("Could not save the overlay")

    np.savez_compressed(
        output_dir / "masks.npz", masks=masks.astype(np.uint8)
    )

    findings = []
    for class_id, mask in enumerate(masks):
        if not np.any(mask):
            continue
        findings.append({
            "class_name": mapping[str(class_id)],
            "retained_regions": int(region_counts[class_id]),
            "approximate_mask_area_percent": round(
                100 * np.count_nonzero(mask) / mask.size, 2
            ),
        })

    result = {
        "inspection_id": inspection_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "report_status": "draft_for_human_review",
        "image_id": path.name,
        "deployment_name": DEPLOYMENT_NAME,
        "model_version": None,
        "detected_classes": detected_classes,
        "findings": findings,
        "overlay_path": str(overlay_path),
        "settings": {
            "probability_threshold_exclusive": 0.5,
            "min_region_pixels_exclusive": 200,
            "region_filter_resolution": [128, 128],
        },
        "timing_ms": {
            "inference_ms": round(inference_ms, 2),
            "inspection_before_json_save": round(
                (perf_counter() - started) * 1000, 2
            ),
        },
        "limitations": [
            "Masks and affected areas are approximate.",
            "Region counts describe mask components, not confirmed defects.",
            "No detected class does not prove the material is defect-free.",
            "This result does not authorize accepting or rejecting material.",
        ],
    }

    result_path = output_dir / "result.json"
    temporary_path = output_dir / "result.json.tmp"
    temporary_path.write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    temporary_path.replace(result_path)
    return result