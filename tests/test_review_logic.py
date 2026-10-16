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
        self.assertIsNone(self.flag("scratches_86.jpg", ["Scratches"]))
        self.assertEqual(
            self.flag("patches_274.jpg", ["Patches", "Pitted surface"]),
            "extra_class",
        )
        self.assertEqual(
            self.flag("patches_28.jpg", ["Scratches"]), "expected_missing"
        )
        self.assertEqual(self.flag("patches_28.jpg", []), "no_detection")

    def test_rows_and_status(self):
        iid = "b" * 32
        rows = rl.build_rows(
            {"crazing_151.jpg": result("crazing_151.jpg", ["Crazing"], iid)},
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


if __name__ == "__main__":
    unittest.main()
