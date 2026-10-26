import numpy as np

from src import inspection
from src.postprocessing import postprocess_output
from src.preprocessing import preprocess_image


def compute_logits(image_path):
    tensor, original = preprocess_image(image_path)
    logits = inspection._get_model().predict(tensor)
    if logits.shape != (1, 6, 128, 128):
        raise ValueError(f"Unexpected output shape: {logits.shape}")
    if not np.isfinite(logits).all():
        raise ValueError("Model returned non-finite values")
    return logits, original


def findings_at(logits, original_shape, threshold, min_size, mapping):
    masks, region_counts = postprocess_output(
        logits, original_shape, threshold=threshold, min_size=min_size
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
    return masks, findings


def diff_findings(base, new):
    base_by = {f["class_name"]: f for f in base}
    new_by = {f["class_name"]: f for f in new}
    rows = []
    for name in [*base_by, *(n for n in new_by if n not in base_by)]:
        a, b = base_by.get(name), new_by.get(name)
        if a and not b:
            change = "removed"
        elif b and not a:
            change = "added"
        elif (
            a["retained_regions"] == b["retained_regions"]
            and a["approximate_mask_area_percent"]
            == b["approximate_mask_area_percent"]
        ):
            change = "same"
        else:
            change = "changed"
        rows.append({
            "class_name": name,
            "regions_recorded": a["retained_regions"] if a else None,
            "regions_what_if": b["retained_regions"] if b else None,
            "area_recorded": a["approximate_mask_area_percent"] if a else None,
            "area_what_if": b["approximate_mask_area_percent"] if b else None,
            "change": change,
        })
    return rows
