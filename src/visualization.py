# Imports
from collections.abc import Mapping
import cv2
import numpy as np


# Colors use OpenCV's BGR order
CLASS_COLORS = [
    (255, 120, 0),
    (0, 165, 255),
    (180, 0, 180),
    (0, 0, 255),
    (0, 200, 0),
    (255, 0, 255),
]


def create_defect_overlay(
    image: np.ndarray,
    masks: np.ndarray,
    class_mapping: Mapping[str, str],
    alpha: float = 0.35,
) -> tuple[np.ndarray, list[str]]:
    """Overlay detected defect masks and labels on the original image."""

    expected_shape = (6, image.shape[0], image.shape[1])

    if masks.shape != expected_shape:
        raise ValueError(
            f"Expected mask shape {expected_shape}, received {masks.shape}"
        )

    colour_layer = image.copy()
    detected_classes = []

    for class_id, mask in enumerate(masks):
        if not np.any(mask):
            continue

        class_name = class_mapping[str(class_id)]
        colour = CLASS_COLORS[class_id]
        detected_classes.append(class_name)

        colour_layer[mask.astype(bool)] = colour

    result = cv2.addWeighted(
        image,
        1.0 - alpha,
        colour_layer,
        alpha,
        0,
    )

    for class_id, mask in enumerate(masks):
        if not np.any(mask):
            continue

        class_name = class_mapping[str(class_id)]
        colour = CLASS_COLORS[class_id]

        contours, _ = cv2.findContours(
            mask.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        cv2.drawContours(result, contours, -1, colour, 2)

        for contour in contours:
            x, y, _, _ = cv2.boundingRect(contour)
            cv2.putText(
                result,
                class_name,
                (x, max(y - 6, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                colour,
                1,
                cv2.LINE_AA,
            )

    return result, detected_classes