import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import llm_config


class LlmConfigTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "outputs" / "llm_config.json"

        path_patch = patch.object(llm_config, "CONFIG_PATH", self.path)
        path_patch.start()
        self.addCleanup(path_patch.stop)

        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("QC_LLM_BASE_URL", None)
        os.environ.pop("QC_LLM_MODEL", None)

    def test_nothing_set_returns_blanks(self):
        self.assertEqual(llm_config.load(), ("", ""))

    def test_save_then_load_round_trips(self):
        llm_config.save("  https://llm.test/openai/v1 ", " my-model ")
        self.assertEqual(
            llm_config.load(), ("https://llm.test/openai/v1", "my-model")
        )

    def test_saved_values_beat_environment(self):
        os.environ["QC_LLM_BASE_URL"] = "https://env.test/v1"
        os.environ["QC_LLM_MODEL"] = "env-model"
        llm_config.save("https://saved.test/v1", "saved-model")
        self.assertEqual(
            llm_config.load(), ("https://saved.test/v1", "saved-model")
        )

    def test_environment_used_without_file(self):
        os.environ["QC_LLM_BASE_URL"] = " https://env.test/v1 "
        os.environ["QC_LLM_MODEL"] = " env-model "
        self.assertEqual(
            llm_config.load(), ("https://env.test/v1", "env-model")
        )

    def test_corrupt_file_falls_back_to_environment(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        os.environ["QC_LLM_BASE_URL"] = "https://env.test/v1"
        os.environ["QC_LLM_MODEL"] = "env-model"
        self.assertEqual(
            llm_config.load(), ("https://env.test/v1", "env-model")
        )

    def test_non_object_file_is_ignored(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps(["x"]), encoding="utf-8")
        self.assertEqual(llm_config.load(), ("", ""))

    def test_save_rejects_invalid_values(self):
        for url, model in (
            ("", "m"),
            ("https://llm.test/v1", ""),
            ("   ", "m"),
            ("ftp://llm.test/v1", "m"),
            ("llm.test/v1", "m"),
        ):
            with self.subTest(url=url, model=model):
                with self.assertRaises(ValueError):
                    llm_config.save(url, model)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
