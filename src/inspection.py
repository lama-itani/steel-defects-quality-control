# Imports
import json
import os
from pathlib import Path
from time import perf_counter

from datetime import datetime, timezone
from uuid import uuid4

import cmlapi
import cv2
import numpy as np
import requests

from src.preprocessing import preprocess_image
from src.postprocessing import postprocess_output
from src.visualization import create_defect_overlay


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "steel-defect-onnx-api-v4"
URL = (
    "https://modelservice.ml-a60a2d26-d1f."
    "applied.jmgjgh.a0.cloudera.site/model"
)


def inspect_image(image_path: str) -> dict:
    """Inspect one image through the validated deployed ONNX endpoint."""
    started = perf_counter()
    path = Path(image_path)
    if not path.is_absolute():
        path = ROOT / path

    tensor, original = preprocess_image(path)

    models = cmlapi.default_client().list_models(
        project_id=os.environ["CDSW_PROJECT_ID"]
    ).models
    matches = [model for model in models if model.name == MODEL_NAME]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one {MODEL_NAME} deployment; found {len(matches)}"
        )

    access_key = matches[0].access_key
    api_key = os.environ["CDSW_APIV2_KEY"]

    request_started = perf_counter()
    response = requests.post(
        URL,
        json={
            "accessKey": access_key,
            "request": {"input": tensor.tolist()},
        },
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    endpoint_ms = (perf_counter() - request_started) * 1000

    if not response.ok:
        error = response.text
        for secret in (access_key, api_key):
            if secret:
                error = error.replace(secret, "[redacted]")
        raise RuntimeError(
            f"Endpoint HTTP {response.status_code}: {error[:800]}"
        )

    body = response.json()
    payload = body.get("response", body) if isinstance(body, dict) else body
    if not isinstance(payload, dict) or "output" not in payload:
        raise ValueError("Expected an endpoint payload containing 'output'")

    logits = np.asarray(payload["output"], dtype=np.float32)
    if logits.shape != (1, 6, 128, 128):
        raise ValueError(f"Unexpected output shape: {logits.shape}")
    if not np.isfinite(logits).all():
        raise ValueError("Endpoint returned non-finite values")

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
        "deployment_name": MODEL_NAME,
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
            "endpoint_round_trip": round(endpoint_ms, 2),
            "inspection_before_json_save": round(
                (perf_counter() - started) * 1000, 2
            ),
        },
        "limitations": [
            "Masks and affected areas are approximate.",
            "Region counts describe mask components, not confirmed defects.",
            "No detected class does not prove the material is defect-free.",
            "Underlying registry version has not been verified.",
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