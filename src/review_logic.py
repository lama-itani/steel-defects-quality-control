from src.catalog import SAMPLE_FILES, expected_class

REVIEWED = {"agree", "disagree", "unsure"}


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
