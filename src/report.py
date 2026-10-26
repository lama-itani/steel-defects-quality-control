import base64
from datetime import datetime, timezone
from html import escape

import cv2

CSS = """
body { font-family: Arial, sans-serif; margin: 24px; color: #111; }
.banner { border: 3px solid #b45309; padding: 10px; font-weight: bold;
  background: #fff7ed; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 16px; }
th, td { border: 1px solid #999; padding: 4px 8px; text-align: left;
  vertical-align: top; }
th { width: 30%; background: #f3f4f6; }
.images { display: flex; gap: 16px; }
.images figure { flex: 1; margin: 0; }
.images img { width: 100%; height: auto; }
.note { white-space: pre-wrap; }
@media print {
  body { margin: 0; }
  th { background: none; }
  .banner { background: none; }
  table, tr, figure { page-break-inside: avoid; }
}
"""


def _text(value):
    return escape(str(value))


def _image(figure_caption, image):
    ok, buffer = (False, None) if image is None else cv2.imencode(".png", image)
    if not ok:
        body = "<p>Image unavailable</p>"
    else:
        data = base64.b64encode(buffer.tobytes()).decode("ascii")
        body = (
            f'<img alt="{_text(figure_caption)}" '
            f'src="data:image/png;base64,{data}">'
        )
    return f"<figure><figcaption>{_text(figure_caption)}</figcaption>{body}</figure>"


def _rows(pairs):
    return "".join(
        f"<tr><th>{_text(k)}</th><td>{_text(v)}</td></tr>" for k, v in pairs
    )


def build_record_html(
    result, history, expected_class, flag_label, original_bgr, overlay_bgr
) -> str:
    settings = result.get("settings", {})
    timing = result.get("timing_ms", {})
    model_version = result.get("model_version")
    resolution = settings.get("region_filter_resolution")
    if isinstance(resolution, (list, tuple)):
        resolution = " x ".join(str(v) for v in resolution)

    trace = _rows([
        ("Inspection ID", result.get("inspection_id")),
        ("Created at", result.get("created_at")),
        ("Deployment", result.get("deployment_name")),
        ("Model version", "not recorded" if model_version is None else model_version),
        ("Probability threshold (exclusive)", settings.get("probability_threshold_exclusive")),
        ("Minimum region (exclusive, px)", settings.get("min_region_pixels_exclusive")),
        ("Region filter resolution", resolution),
        ("Inference (ms)", timing.get("inference_ms")),
        ("Record generated at (UTC)", datetime.now(timezone.utc).isoformat()),
    ])

    detected = result.get("detected_classes") or []
    summary = _rows([
        ("Expected class", expected_class),
        ("Detected classes", ", ".join(detected) or "None"),
        ("Flag", flag_label or "None"),
    ])

    findings = result.get("findings") or []
    if findings:
        finding_rows = "".join(
            f"<tr><td>{_text(f.get('class_name'))}</td>"
            f"<td>{_text(f.get('retained_regions'))}</td>"
            f"<td>{_text(f.get('approximate_mask_area_percent'))}</td></tr>"
            for f in findings
        )
        findings_html = (
            "<table><tr><th>Class</th><th>Retained regions</th>"
            f"<th>Approx. area (%)</th></tr>{finding_rows}</table>"
        )
    else:
        findings_html = (
            "<p>No retained detections. This does not mean defect-free.</p>"
        )

    if history:
        history_rows = "".join(
            f"<tr><td>{_text(str(h.get('verdict', '')).capitalize())}</td>"
            f"<td>{_text(h.get('reviewed_at', ''))}</td>"
            f"<td class='note'>{_text(h.get('note', ''))}</td></tr>"
            for h in history
        )
        history_html = (
            "<table><tr><th>Verdict</th><th>Time</th><th>Note</th></tr>"
            f"{history_rows}</table>"
        )
    else:
        history_html = "<p>Not reviewed.</p>"

    limitations = "".join(
        f"<li>{_text(item)}</li>" for item in result.get("limitations", [])
    )

    image_id = _text(result.get("image_id"))
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>Inspection record {image_id}</title>"
        f"<style>{CSS}</style></head><body>"
        "<div class='banner'>DRAFT – FOR HUMAN REVIEW. This record does not "
        "accept or reject material.</div>"
        f"<h1>Steel surface inspection record</h1><h2>{image_id}</h2>"
        f"<table>{trace}</table>"
        "<div class='images'>"
        f"{_image('Original', original_bgr)}{_image('Overlay', overlay_bgr)}"
        "</div>"
        f"<table>{summary}</table>"
        f"<h3>Findings</h3>{findings_html}"
        f"<h3>Review history</h3>{history_html}"
        f"<h3>Limitations</h3><ul>{limitations}</ul>"
        "</body></html>"
    )
