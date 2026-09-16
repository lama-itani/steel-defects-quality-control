# Imports
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.inference import OnnxDefectModel
from src.postprocessing import postprocess_output
from src.preprocessing import preprocess_image
from src.visualization import create_defect_overlay


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run steel-defect detection locally."
    )
    parser.add_argument(
        "images",
        nargs="+",
        type=Path,
        help="One or more images to inspect.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=PROJECT_ROOT / "model" / "Unet.onnx",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    mapping_path = PROJECT_ROOT / "config" / "class_mapping.json"
    with mapping_path.open(encoding="utf-8") as file:
        class_mapping = json.load(file)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Load once, then reuse for every image.
    model = OnnxDefectModel(args.model)

    for image_path in args.images:
        tensor, original = preprocess_image(image_path)

        start = perf_counter()
        logits = model.predict(tensor)
        inference_ms = (perf_counter() - start) * 1000

        masks, region_counts = postprocess_output(
            logits,
            original.shape[:2],
        )

        overlay, detected_classes = create_defect_overlay(
            original,
            masks,
            class_mapping,
        )

        output_path = args.output_dir / f"{image_path.stem}_overlay.jpg"

        if not cv2.imwrite(str(output_path), overlay):
            raise RuntimeError(f"Failed to save: {output_path}")

        print(f"Image: {image_path}")
        print(f"Detected: {detected_classes or ['No defect']}")
        print(f"Regions by class: {region_counts}")
        print(f"CPU inference: {inference_ms:.2f} ms")
        print(f"Saved: {output_path}")
        print()


if __name__ == "__main__":
    main()