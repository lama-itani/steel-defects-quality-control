from src.catalog import PREFIX_TO_CLASS, SAMPLE_FILES, expected_class

REVIEWED = {"agree", "disagree", "unsure"}
AREA_BANDS = ("<5%", "5–20%", "≥20%")
VERDICT_KEYS = ("agree", "disagree", "unsure", "not_reviewed")


def _flag(expected, detected):
    if not detected:
        return "no_detection"
    if detected == {expected}:
        return None
    return "extra_class" if expected in detected else "expected_missing"


def build_rows(latest: dict, reviews: dict) -> list:
    """One row per catalog image; reviews maps inspection_id to a review."""
    rows = []
    for name in SAMPLE_FILES:
        expected = expected_class(name)
        result = latest.get(name)
        row = {
            "image_id": name,
            "expected_class": expected,
            "inspection_id": None,
            "detected_classes": [],
            "findings": [],
            "status": "not_inspected",
            "flag": None,
        }
        if result:
            iid = result["inspection_id"]
            detected = list(result.get("detected_classes", []))
            review = reviews.get(iid)
            row.update(
                inspection_id=iid,
                detected_classes=detected,
                findings=result.get("findings", []),
                status=review["verdict"] if review else "not_reviewed",
                flag=_flag(expected, set(detected)),
            )
        rows.append(row)
    return rows


def filter_rows(rows, class_name=None, mismatch_only=False, status=None):
    return [
        r for r in rows
        if (not class_name or r["expected_class"] == class_name)
        and (not mismatch_only or r["flag"])
        and (not status or r["status"] == status)
    ]


def summary(rows) -> dict:
    return {
        "total": len(rows),
        "expected_detected": sum(
            r["expected_class"] in r["detected_classes"] for r in rows
        ),
        "flagged": sum(bool(r["flag"]) for r in rows),
        "reviewed": sum(r["status"] in REVIEWED for r in rows),
    }


def _area_band(percent):
    if percent < 5:
        return AREA_BANDS[0]
    if percent < 20:
        return AREA_BANDS[1]
    return AREA_BANDS[2]


def dashboard_stats(rows) -> dict:
    """Aggregate figures for the QC dashboard; only inspected rows count."""
    classes = list(PREFIX_TO_CLASS.values())
    inspected = [r for r in rows if r["inspection_id"]]

    images = {c: 0 for c in classes}
    regions = {c: 0 for c in classes}
    bands = {c: dict.fromkeys(AREA_BANDS, 0) for c in classes}
    for r in inspected:
        for c in set(r["detected_classes"]):
            images[c] = images.get(c, 0) + 1
        for f in r["findings"]:
            c = f["class_name"]
            regions[c] = regions.get(c, 0) + f["retained_regions"]
            bands.setdefault(c, dict.fromkeys(AREA_BANDS, 0))[
                _area_band(f["approximate_mask_area_percent"])
            ] += 1

    pareto = sorted(
        (
            {"class_name": c, "images": n, "regions": regions.get(c, 0)}
            for c, n in images.items() if n
        ),
        key=lambda p: (p["images"], p["regions"]),
        reverse=True,
    )

    per_class = {}
    for c in classes:
        group = [r for r in inspected if r["expected_class"] == c]
        hit = sum(c in r["detected_classes"] for r in group)
        entry = {
            "images": sum(r["expected_class"] == c for r in rows),
            "inspected": len(group),
            "expected_detected": hit,
            "detection_rate": hit / len(group) if group else None,
        }
        for key in VERDICT_KEYS:
            entry[key] = sum(r["status"] == key for r in group)
        per_class[c] = entry

    attention = [
        r["image_id"] for r in inspected
        if r["flag"] or r["status"] == "disagree"
    ]
    return {
        "inspected": len(inspected),
        "pareto": pareto,
        "area_bands": {c: bands[c] for c in classes},
        "per_class": per_class,
        "attention": attention,
    }


def neighbours(filtered_rows, image_id):
    ids = [r["image_id"] for r in filtered_rows]
    if image_id not in ids:
        return None, None
    i = ids.index(image_id)
    return (ids[i - 1] if i > 0 else None,
            ids[i + 1] if i + 1 < len(ids) else None)


def next_unreviewed(filtered_rows, after_image_id=None):
    """First 'not_reviewed' row after the given image, wrapping around."""
    ids = [r["image_id"] for r in filtered_rows]
    start = ids.index(after_image_id) + 1 if after_image_id in ids else 0
    for r in filtered_rows[start:] + filtered_rows[:start]:
        if r["status"] == "not_reviewed" and r["image_id"] != after_image_id:
            return r["image_id"]
    return None
