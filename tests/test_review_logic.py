import unittest

from src import review_logic as rl
from src.catalog import SAMPLE_FILES


def result(name, detected, iid):
    return {"inspection_id": iid, "detected_classes": detected, "findings": []}


class FlagTests(unittest.TestCase):
    def flag(self, name, detected):
        return rl.build_rows({name: result(name, detected, "a" * 32)}, {})[
            SAMPLE_FILES.index(name)
        ]["flag"]

    def test_flags(self):
        self.assertIsNone(self.flag("scratches_1.jpg", ["Scratches"]))
        self.assertEqual(
            self.flag("rolled-in_scale_4.jpg", ["Rolled-in scale", "Pitted surface"]),
            "extra_class",
        )
        self.assertEqual(
            self.flag("patches_1.jpg", ["Scratches"]), "expected_missing"
        )
        self.assertEqual(self.flag("patches_1.jpg", []), "no_detection")

    def test_rows_and_status(self):
        iid = "b" * 32
        rows = rl.build_rows(
            {"crazing_1.jpg": result("crazing_1.jpg", ["Crazing"], iid)},
            {iid: {"verdict": "agree"}},
        )
        self.assertEqual([r["image_id"] for r in rows], SAMPLE_FILES)
        self.assertEqual(rows[0]["status"], "agree")
        self.assertEqual(rows[1]["status"], "not_inspected")
        s = rl.summary(rows)
        self.assertEqual(
            (s["total"], s["expected_detected"], s["flagged"], s["reviewed"]),
            (29, 1, 0, 1),
        )


class NavTests(unittest.TestCase):
    def rows(self, statuses):
        return [
            {"image_id": f"i{n}", "expected_class": "Crazing", "flag": None,
             "detected_classes": [], "status": s}
            for n, s in enumerate(statuses)
        ]

    def test_filter(self):
        rows = rl.build_rows({}, {})
        self.assertEqual(len(rl.filter_rows(rows, class_name="Inclusion")), 4)
        self.assertEqual(rl.filter_rows(rows, mismatch_only=True), [])
        self.assertEqual(len(rl.filter_rows(rows, status="not_inspected")), 29)

    def test_neighbours(self):
        rows = self.rows(["agree"] * 3)
        self.assertEqual(rl.neighbours(rows, "i0"), (None, "i1"))
        self.assertEqual(rl.neighbours(rows, "i2"), ("i1", None))
        self.assertEqual(rl.neighbours(rows, "zz"), (None, None))

    def test_next_unreviewed(self):
        rows = self.rows(["not_reviewed", "agree", "not_reviewed", "agree"])
        self.assertEqual(rl.next_unreviewed(rows), "i0")
        self.assertEqual(rl.next_unreviewed(rows, "i0"), "i2")
        self.assertEqual(rl.next_unreviewed(rows, "i2"), "i0")
        done = self.rows(["agree", "unsure"])
        self.assertIsNone(rl.next_unreviewed(done, "i0"))


def finding(name, regions, area):
    return {
        "class_name": name,
        "retained_regions": regions,
        "approximate_mask_area_percent": area,
    }


def drow(image, expected, findings, status="not_reviewed", flag=None, iid="x"):
    return {
        "image_id": image,
        "expected_class": expected,
        "inspection_id": iid,
        "detected_classes": [f["class_name"] for f in findings],
        "findings": findings,
        "status": status,
        "flag": flag,
    }


class DashboardTests(unittest.TestCase):
    def test_pareto_order_and_counts(self):
        rows = [
            drow("a", "Crazing", [finding("Crazing", 2, 1.0)]),
            drow("b", "Crazing", [
                finding("Crazing", 1, 1.0), finding("Patches", 5, 1.0),
            ]),
            drow("c", "Patches", [finding("Patches", 1, 1.0)]),
            drow("d", "Patches", [finding("Patches", 1, 1.0)]),
        ]
        pareto = rl.dashboard_stats(rows)["pareto"]
        self.assertEqual(
            pareto,
            [
                {"class_name": "Patches", "images": 3, "regions": 7},
                {"class_name": "Crazing", "images": 2, "regions": 3},
            ],
        )

    def test_area_band_boundaries(self):
        rows = [drow("a", "Crazing", [
            finding("Crazing", 1, 4.99),
            finding("Patches", 1, 5.0),
            finding("Scratches", 1, 20.0),
        ])]
        bands = rl.dashboard_stats(rows)["area_bands"]
        self.assertEqual(bands["Crazing"], {"<5%": 1, "5–20%": 0, "≥20%": 0})
        self.assertEqual(bands["Patches"], {"<5%": 0, "5–20%": 1, "≥20%": 0})
        self.assertEqual(bands["Scratches"], {"<5%": 0, "5–20%": 0, "≥20%": 1})

    def test_per_class_rate_and_verdicts(self):
        rows = [
            drow("a", "Crazing", [finding("Crazing", 1, 1.0)], status="agree"),
            drow("b", "Crazing", [], status="disagree", flag="no_detection"),
            drow("c", "Crazing", [], status="unsure", flag="no_detection"),
            drow("d", "Crazing", [finding("Crazing", 1, 1.0)]),
            drow("e", "Patches", [], iid=None, status="not_inspected"),
        ]
        stats = rl.dashboard_stats(rows)["per_class"]
        crazing = stats["Crazing"]
        self.assertEqual(crazing["inspected"], 4)
        self.assertEqual(crazing["expected_detected"], 2)
        self.assertEqual(crazing["detection_rate"], 0.5)
        self.assertEqual(
            sum(crazing[k] for k in
                ("agree", "disagree", "unsure", "not_reviewed")),
            crazing["inspected"],
        )
        self.assertIsNone(stats["Patches"]["detection_rate"])
        self.assertEqual(stats["Patches"]["inspected"], 0)

    def test_attention(self):
        rows = [
            drow("a", "Crazing", [finding("Crazing", 1, 1.0)], status="agree"),
            drow("b", "Patches", [], flag="no_detection"),
            drow("c", "Inclusion", [finding("Inclusion", 1, 1.0)],
                 status="disagree"),
        ]
        self.assertEqual(rl.dashboard_stats(rows)["attention"], ["b", "c"])

    def test_empty(self):
        stats = rl.dashboard_stats(rl.build_rows({}, {}))
        self.assertEqual(stats["pareto"], [])
        self.assertEqual(stats["attention"], [])
        self.assertEqual(stats["inspected"], 0)


if __name__ == "__main__":
    unittest.main()
