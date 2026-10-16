import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import qc_tools

CLASS_NAMES = sorted(qc_tools.CLASSES)


def make_document(statuses=None, extra_source=None):
    statuses = statuses or {}
    classes = {}
    for name in CLASS_NAMES:
        status = statuses.get(name, "approved")
        classes[name] = {
            "status": status,
            "definition": f"{name} definition" if status != "guidance unavailable" else None,
            "typical_causes": ["cause"],
            "class_specific_handling": ["specific"],
            "sources": ["SRC-A 2.1", "SRC-B"],
        }
    if extra_source:
        classes[CLASS_NAMES[0]]["sources"].append(extra_source)
    return {
        "document": {"version": "9.9", "status": "approved"},
        "sources": {
            "SRC-A": {
                "citation": "Source A", "url": "https://a.example",
                "access": "free",
            },
            "SRC-B": {
                "citation": "Source B", "url": "https://b.example",
                "access": "paid",
            },
        },
        "common_handling": {"steps": ["1. confirm"], "sources": ["SRC-A"]},
        "classes": classes,
    }


class GuidanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("QC_SHOW_DRAFT_GUIDANCE", None)

    def write(self, content, name="g.json"):
        path = Path(self.tmp.name) / name
        path.write_text(
            content if isinstance(content, str) else json.dumps(content),
            encoding="utf-8",
        )
        return path

    def lookup(self, document, defect_class):
        loaded = qc_tools._load_guidance(self.write(document))
        with patch.object(qc_tools, "GUIDANCE", loaded):
            return qc_tools.lookup_defect_guidance(defect_class)

    def assert_unavailable(self, result, defect_class):
        self.assertEqual(result, {
            "defect_class": defect_class,
            "status": "guidance unavailable",
            "guidance": None,
            "source": None,
            "version": None,
        })

    def test_approved_returns_content_and_resolved_sources(self):
        result = self.lookup(make_document(), "Scratches")

        self.assertEqual(
            set(result),
            {"defect_class", "status", "guidance", "source", "version"},
        )
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["version"], "9.9")
        self.assertEqual(
            result["guidance"],
            {
                "definition": "Scratches definition",
                "typical_causes": ["cause"],
                "common_handling": ["1. confirm"],
                "class_specific_handling": ["specific"],
            },
        )
        self.assertEqual(
            result["source"],
            [
                {"citation": "Source A", "section": "2.1",
                 "url": "https://a.example", "access": "free"},
                {"citation": "Source B", "section": None,
                 "url": "https://b.example", "access": "paid"},
            ],
        )

    def test_draft_hidden_by_default(self):
        document = make_document({"Scratches": "draft_pending_review"})
        self.assert_unavailable(self.lookup(document, "Scratches"), "Scratches")

    def test_draft_shown_with_flag(self):
        document = make_document({"Scratches": "draft_pending_review"})
        os.environ["QC_SHOW_DRAFT_GUIDANCE"] = "1"
        result = self.lookup(document, "Scratches")

        self.assertEqual(result["status"], "draft_pending_review")
        self.assertIsNotNone(result["guidance"])
        self.assertEqual(len(result["source"]), 2)

    def test_flag_other_than_one_keeps_draft_hidden(self):
        document = make_document({"Scratches": "draft_pending_review"})
        os.environ["QC_SHOW_DRAFT_GUIDANCE"] = "true"
        self.assert_unavailable(self.lookup(document, "Scratches"), "Scratches")

    def test_flag_does_not_expose_unavailable_class(self):
        document = make_document({"Patches": "guidance unavailable"})
        os.environ["QC_SHOW_DRAFT_GUIDANCE"] = "1"
        self.assert_unavailable(self.lookup(document, "Patches"), "Patches")

    def test_unknown_class_raises(self):
        loaded = qc_tools._load_guidance(self.write(make_document()))
        with patch.object(qc_tools, "GUIDANCE", loaded):
            for value in ("Dents", "", None, 3):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        qc_tools.lookup_defect_guidance(value)

    def test_missing_file_falls_back(self):
        missing = Path(self.tmp.name) / "absent.json"
        self.assertIsNone(qc_tools._load_guidance(missing))
        with patch.object(qc_tools, "GUIDANCE", None):
            for name in CLASS_NAMES:
                self.assert_unavailable(
                    qc_tools.lookup_defect_guidance(name), name
                )

    def test_malformed_file_falls_back(self):
        for content in ("{not json", "[]", '{"document": {}}'):
            with self.subTest(content=content):
                self.assertIsNone(
                    qc_tools._load_guidance(self.write(content))
                )

    def test_class_mismatch_falls_back(self):
        document = make_document()
        del document["classes"][CLASS_NAMES[0]]
        self.assertIsNone(qc_tools._load_guidance(self.write(document)))

        document = make_document()
        document["classes"]["Dents"] = document["classes"][CLASS_NAMES[0]]
        self.assertIsNone(qc_tools._load_guidance(self.write(document)))

    def test_invalid_class_status_rejected(self):
        document = make_document({"Scratches": "maybe"})
        self.assertIsNone(qc_tools._load_guidance(self.write(document)))

    def test_unknown_source_id_rejected_at_load(self):
        document = make_document(extra_source="SRC-X 1.1")
        self.assertIsNone(qc_tools._load_guidance(self.write(document)))

        document = make_document()
        document["common_handling"]["sources"] = ["SRC-X"]
        self.assertIsNone(qc_tools._load_guidance(self.write(document)))

    def test_real_file_passes_validation(self):
        loaded = qc_tools._load_guidance(qc_tools.GUIDANCE_PATH)

        self.assertIsNotNone(loaded)
        self.assertEqual(set(loaded["classes"]), set(qc_tools.CLASSES))
        self.assertIsNotNone(qc_tools.GUIDANCE)

    def test_real_file_default_hides_drafts_and_flag_shows_them(self):
        self.assert_unavailable(
            qc_tools.lookup_defect_guidance("Pitted surface"), "Pitted surface"
        )
        os.environ["QC_SHOW_DRAFT_GUIDANCE"] = "1"
        draft = qc_tools.lookup_defect_guidance("Pitted surface")
        self.assertEqual(draft["status"], "draft_pending_review")
        self.assertTrue(draft["source"])
        self.assert_unavailable(
            qc_tools.lookup_defect_guidance("Patches"), "Patches"
        )


if __name__ == "__main__":
    unittest.main()
