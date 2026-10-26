import unittest

import numpy as np

from src.report import build_record_html

IID = "a" * 32


def make_result(**overrides):
    result = {
        "inspection_id": IID,
        "created_at": "2026-01-01T00:00:00+00:00",
        "image_id": "scratches_1.jpg",
        "deployment_name": "local-onnx",
        "model_version": "v1",
        "detected_classes": ["Scratches", "Patches"],
        "findings": [
            {"class_name": "Scratches", "retained_regions": 2,
             "approximate_mask_area_percent": 3.5},
            {"class_name": "Patches", "retained_regions": 1,
             "approximate_mask_area_percent": 12.0},
        ],
        "settings": {
            "probability_threshold_exclusive": 0.5,
            "min_region_pixels_exclusive": 200,
            "region_filter_resolution": [128, 128],
        },
        "timing_ms": {"inference_ms": 10.0},
        "limitations": ["Masks and affected areas are approximate."],
    }
    result.update(overrides)
    return result


IMG = np.zeros((10, 10, 3), np.uint8)


def build(result=None, history=(), original=IMG, overlay=IMG):
    return build_record_html(
        result or make_result(), list(history), "Scratches", "Extra class detected",
        original, overlay,
    )


class RecordTests(unittest.TestCase):
    def test_core_content(self):
        page = build()
        self.assertIn(IID, page)
        self.assertIn("DRAFT – FOR HUMAN REVIEW", page)
        self.assertIn("Scratches", page)
        self.assertIn("Patches", page)
        self.assertIn("data:image/png;base64,", page)
        self.assertIn("Not reviewed.", page)

    def test_note_is_escaped(self):
        history = [{
            "verdict": "disagree",
            "reviewed_at": "2026-01-02T00:00:00+00:00",
            "note": "<script>alert(1)</script>",
        }]
        page = build(history=history)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", page)

    def test_model_version_none(self):
        self.assertIn("not recorded", build(make_result(model_version=None)))

    def test_missing_image(self):
        page = build(original=None)
        self.assertIn("Image unavailable", page)

    def test_no_findings(self):
        page = build(make_result(findings=[], detected_classes=[]))
        self.assertIn("does not mean defect-free", page)


if __name__ == "__main__":
    unittest.main()
