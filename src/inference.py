# Imports
from pathlib import Path
import numpy as np
import onnxruntime as ort


EXPECTED_INPUT_SHAPE = (1, 3, 128, 128)


class OnnxDefectModel:
    """Load the ONNX model once and run CPU inference."""

    def __init__(self, model_path: str | Path):
        model_path = Path(model_path)

        if not model_path.is_file():
            raise FileNotFoundError(f"Model not found: {model_path}")

        self.session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )

        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict(self, input_tensor: np.ndarray) -> np.ndarray:
        if input_tensor.shape != EXPECTED_INPUT_SHAPE:
            raise ValueError(
                f"Expected shape {EXPECTED_INPUT_SHAPE}, "
                f"received {input_tensor.shape}"
            )

        if input_tensor.dtype != np.float32:
            raise TypeError(
                f"Expected float32 input, received {input_tensor.dtype}"
            )

        output = self.session.run(
            [self.output_name],
            {self.input_name: input_tensor},
        )[0]

        return output