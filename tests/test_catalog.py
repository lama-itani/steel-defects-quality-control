import unittest
from collections import Counter

from src import catalog


class CatalogTests(unittest.TestCase):
    def test_unique_and_counts(self):
        files = catalog.SAMPLE_FILES
        self.assertEqual(len(files), 29)
        self.assertEqual(len(set(files)), 29)
        counts = Counter(catalog.expected_class(f) for f in files)
        self.assertEqual(
            [counts[c] for c in catalog.PREFIX_TO_CLASS.values()],
            [5, 5, 4, 5, 5, 5],
        )

    def test_expected_class(self):
        cases = {
            "crazing_1.jpg": "Crazing",
            "patches_1.jpg": "Patches",
            "inclusion_1.jpg": "Inclusion",
            "pitted_surface_1.jpg": "Pitted surface",
            "rolled-in_scale_1.jpg": "Rolled-in scale",
            "scratches_1.jpg": "Scratches",
        }
        for name, cls in cases.items():
            self.assertEqual(catalog.expected_class(name), cls)

    def test_unknown_name(self):
        for bad in ("unknown_1.jpg", "crazing.jpg", "../crazing_1.jpg"):
            with self.assertRaises(ValueError):
                catalog.expected_class(bad)
        with self.assertRaises(ValueError):
            catalog.sample_path("crazing_999.jpg")

    def test_qc_tools_samples_match(self):
        try:
            from src import qc_tools
        except ModuleNotFoundError as e:
            self.skipTest(f"missing {e.name}")

        self.assertEqual(set(qc_tools.SAMPLES), set(catalog.SAMPLE_FILES))

    def test_sample_path(self):
        p = catalog.sample_path("crazing_1.jpg")
        self.assertEqual(p, catalog.ROOT / "data" / "crazing_1.jpg")


if __name__ == "__main__":
    unittest.main()
