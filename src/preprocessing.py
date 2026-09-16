# Imports
from pathlib import Path
import cv2
import numpy as np


INPUT_SIZE = (128, 128)

# Values used during the original model training.
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_image(image_path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Load and prepare one image for the ONNX model."""

    original_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)

    if original_image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    # Preserve OpenCV's BGR channel order.
    normalized = original_image.astype(np.float32) / 255.0
    normalized = (normalized - MEAN) / STD

    resized = cv2.resize(
        normalized,
        INPUT_SIZE,
        interpolation=cv2.INTER_LINEAR,
    )

    # HWC -> NCHW: [128, 128, 3] -> [1, 3, 128, 128]
    input_tensor = resized.transpose(2, 0, 1)[None, ...]
    input_tensor = np.ascontiguousarray(input_tensor, dtype=np.float32)

    return input_tensor, original_image