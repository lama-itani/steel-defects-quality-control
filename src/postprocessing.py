# Imports
import cv2
import numpy as np


EXPECTED_OUTPUT_SHAPE = (1, 6, 128, 128)


def sigmoid(values: np.ndarray) -> np.ndarray:
    """Convert model logits into probabilities."""
    values = values.astype(np.float32, copy=False)
    probabilities = np.empty_like(values)

    positive = values >= 0
    probabilities[positive] = 1.0 / (1.0 + np.exp(-values[positive]))

    exp_values = np.exp(values[~positive])
    probabilities[~positive] = exp_values / (1.0 + exp_values)

    return probabilities


def remove_small_regions(
    mask: np.ndarray,
    min_size: int,
) -> tuple[np.ndarray, int]:
    """Keep connected regions containing more than min_size pixels."""
    component_count, labels = cv2.connectedComponents(
        mask.astype(np.uint8)
    )

    filtered_mask = np.zeros_like(mask, dtype=np.uint8)
    retained_count = 0

    for component_id in range(1, component_count):
        region = labels == component_id

        if np.count_nonzero(region) > min_size:
            filtered_mask[region] = 1
            retained_count += 1

    return filtered_mask, retained_count


def postprocess_output(
    logits: np.ndarray,
    original_shape: tuple[int, int],
    threshold: float = 0.5,
    min_size: int = 200,
) -> tuple[np.ndarray, list[int]]:
    """Create six full-sized binary defect masks."""

    if logits.shape != EXPECTED_OUTPUT_SHAPE:
        raise ValueError(
            f"Expected shape {EXPECTED_OUTPUT_SHAPE}, "
            f"received {logits.shape}"
        )

    original_height, original_width = original_shape
    probabilities = sigmoid(logits[0])

    resized_masks = []
    region_counts = []

    for probability in probabilities:
        binary_mask = (probability > threshold).astype(np.uint8)

        filtered_mask, count = remove_small_regions(
            binary_mask,
            min_size,
        )

        resized_mask = cv2.resize(
            filtered_mask,
            (original_width, original_height),
            interpolation=cv2.INTER_NEAREST,
        )

        resized_masks.append(resized_mask)
        region_counts.append(count)

    return np.stack(resized_masks), region_counts