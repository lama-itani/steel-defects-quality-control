from pathlib import Path

import cml.models_v1 as models
import numpy as np

from src.inference import OnnxDefectModel

_model = None


@models.cml_model
def predict(args):
    """Accept a JSON tensor and return the six raw output maps."""
    global _model

    tensor = np.asarray(args["input"], dtype=np.float32)

    if _model is None:
        model_path = Path.cwd() / "model" / "Unet.onnx"
        _model = OnnxDefectModel(model_path)

    return {"output": _model.predict(tensor).tolist()}
