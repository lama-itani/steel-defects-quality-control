import json
import unittest
from pathlib import Path

import numpy as np

from src import what_if

ROOT = Path(__file__).resolve().parents[1]
MAPPING = json.loads((ROOT / "config/class_mapping.json").read_text())
SHAPE = (128, 128)
INSPECTION_KEYS = {
    "class_name", "retained_regions", "approximate_mask_area_percent",
}


def logits_with_block(value):
    logits = np.full((1, 6, 128, 128), -10, np.float32)
    logits[0, 2, 10:30, 10:30] = value
    return logits


class FindingsAtTests(unittest.TestCase):
    def names(self, logits, threshold, min_size):
        _, findings = what_if.findings_at(
            logits, SHAPE, threshold, min_size, MAPPING
        )
        return [f["class_name"] for f in findings]

    def test_threshold(self):
        logits = logits_with_block(0.5)
        self.assertEqual(self.names(logits, 0.5, 200), [MAPPING["2"]])
        self.assertEqual(self.names(logits, 0.7, 200), [])

    def test_min_size(self):
        logits = logits_with_block(5)
        self.assertEqual(self.names(logits, 0.5, 200), [MAPPING["2"]])
        self.assertEqual(self.names(logits, 0.5, 500), [])

    def test_finding_shape(self):
        _, findings = what_if.findings_at(
            logits_with_block(5), SHAPE, 0.5, 200, MAPPING
        )
        self.assertEqual(set(findings[0]), INSPECTION_KEYS)
        self.assertEqual(findings[0]["retained_regions"], 1)
        self.assertEqual(findings[0]["approximate_mask_area_percent"], 2.44)


def f(name, regions, area):
    return {
        "class_name": name,
        "retained_regions": regions,
        "approximate_mask_area_percent": area,
    }


class DiffTests(unittest.TestCase):
    def test_diff(self):
        base = [f("A", 1, 1.0), f("B", 1, 2.0), f("C", 1, 3.0)]
        new = [f("B", 1, 2.0), f("C", 2, 4.0), f("D", 1, 5.0)]
        by = {r["class_name"]: r for r in what_if.diff_findings(base, new)}
        self.assertEqual(by["A"]["change"], "removed")
        self.assertEqual(by["B"]["change"], "same")
        self.assertEqual(by["C"]["change"], "changed")
        self.assertEqual(by["D"]["change"], "added")
        self.assertIsNone(by["A"]["regions_what_if"])
        self.assertIsNone(by["D"]["area_recorded"])


if __name__ == "__main__":
    unittest.main()
