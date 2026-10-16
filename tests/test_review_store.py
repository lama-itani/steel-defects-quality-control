import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    from src import qc_tools, review_store
except ModuleNotFoundError:
    review_store = None

ID = "a" * 32
ID2 = "b" * 32


def write_result(root, iid, image_id, created):
    d = root / iid
    d.mkdir()
    (d / "result.json").write_text(json.dumps({
        "inspection_id": iid, "status": "completed",
        "image_id": image_id, "created_at": created,
    }))


@unittest.skipIf(review_store is None, "missing dependency")
class StoreTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for mod in (qc_tools, review_store):
            p = mock.patch.object(mod, "STORE", self.root)
            p.start()
            self.addCleanup(p.stop)

    def test_masks_round_trip(self):
        (self.root / ID).mkdir()
        masks = np.zeros((6, 4, 5), dtype=np.uint8)
        masks[2, 1, 1] = 1
        np.savez_compressed(self.root / ID / "masks.npz", masks=masks)
        self.assertTrue(np.array_equal(review_store.load_masks(ID), masks))

    def test_masks_missing_invalid_shape(self):
        self.assertIsNone(review_store.load_masks(ID))
        for bad in ("../x", "abc", None):
            with self.assertRaises(ValueError):
                review_store.load_masks(bad)
        (self.root / ID).mkdir()
        np.savez_compressed(self.root / ID / "masks.npz", masks=np.zeros((3, 4, 5)))
        with self.assertRaises(ValueError):
            review_store.load_masks(ID)

    def test_append_and_history(self):
        write_result(self.root, ID, "crazing_151.jpg", "2026-01-01")
        review_store.append_review(ID, "unsure", " first ")
        review_store.append_review(ID, "agree", "")
        hist = review_store.review_history(ID)
        self.assertEqual([h["verdict"] for h in hist], ["agree", "unsure"])
        self.assertEqual(hist[1]["note"], "first")
        self.assertEqual(review_store.latest_review(ID)["verdict"], "agree")

    def test_append_rejects(self):
        write_result(self.root, ID, "crazing_151.jpg", "2026-01-01")
        with self.assertRaises(ValueError):
            review_store.append_review(ID, "maybe", "")
        with self.assertRaises(ValueError):
            review_store.append_review(ID, "disagree", "  ")
        with self.assertRaises(ValueError):
            review_store.append_review(ID, "agree", "x" * 2001)
        with self.assertRaises(ValueError):
            review_store.append_review("bad", "agree", "")
        with self.assertRaises(FileNotFoundError):
            review_store.append_review(ID2, "agree", "")

    def test_bad_line_skipped(self):
        write_result(self.root, ID, "crazing_151.jpg", "2026-01-01")
        review_store.append_review(ID, "agree", "")
        with open(self.root / ID / "reviews.jsonl", "a") as f:
            f.write("{not json\n")
        self.assertEqual(len(review_store.review_history(ID)), 1)

    def test_latest_inspections(self):
        write_result(self.root, ID, "crazing_151.jpg", "2026-01-01")
        write_result(self.root, ID2, "crazing_151.jpg", "2026-02-01")
        write_result(self.root, "c" * 32, "other.jpg", "2026-03-01")
        (self.root / "junk").mkdir()
        latest = review_store.latest_inspections()
        self.assertEqual(list(latest), ["crazing_151.jpg"])
        self.assertEqual(latest["crazing_151.jpg"]["inspection_id"], ID2)


if __name__ == "__main__":
    unittest.main()
