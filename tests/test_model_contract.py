# Imports 
import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.inference import OnnxDefectModel


MODEL_PATH = PROJECT_ROOT / "model" / "Unet.onnx"


class TestModelContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.model = OnnxDefectModel(MODEL_PATH)

    def test_model_metadata(self) -> None:
        model_input = self.model.session.get_inputs()[0]
        model_output = self.model.session.get_outputs()[0]

        self.assertEqual(model_input.shape, [1, 3, 128, 128])
        self.assertEqual(model_input.type, "tensor(float)")
        self.assertEqual(model_output.shape, [1, 6, 128, 128])
        self.assertEqual(model_output.type, "tensor(float)")

    def test_inference_output(self) -> None:
        test_input = np.zeros(
            (1, 3, 128, 128),
            dtype=np.float32,
        )

        output = self.model.predict(test_input)

        self.assertEqual(output.shape, (1, 6, 128, 128))
        self.assertEqual(output.dtype, np.float32)
        self.assertTrue(np.isfinite(output).all())


if __name__ == "__main__":
    unittest.main()