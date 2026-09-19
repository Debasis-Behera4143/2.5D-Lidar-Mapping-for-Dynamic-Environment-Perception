"""
Core data types and input validation contracts for 2.5D LiDAR mapping.

Defines data structures and rigorous validation functions for perception outputs
ingested by the uniform and adaptive grid mappers.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


PROJECT_CLASSES = [
    "road",         # 0
    "sidewalk",     # 1
    "building",     # 2
    "vegetation",   # 3
    "vehicle",      # 4
    "pedestrian",   # 5
    "pole_sign",    # 6
    "other",        # 7
]

NUM_CLASSES = len(PROJECT_CLASSES)


class MappingValidationError(ValueError):
    """Raised when an input perception payload violates mapping contract rules."""
    pass


@dataclass
class ValidatedInput:
    """Normalized, validated input arrays ready for mapping aggregation."""
    points: np.ndarray             # (N, 3) or (N, 4) float32
    predicted_labels: np.ndarray   # (N,) int64 in [0, 7]
    confidence_scores: np.ndarray  # (N,) float32 in [0.0, 1.0]
    frame_id: str
    ground_truth_labels: Optional[np.ndarray] = None  # (N,) int64 in [0, 7]
    intensity: Optional[np.ndarray] = None            # (N,) float32

    @property
    def point_count(self) -> int:
        return len(self.points)


def validate_input_payload(payload: Dict[str, Any]) -> ValidatedInput:
    """
    Validate perception output payload against the strict project contract:
    - points must have shape (N, 3) or (N, 4) with N > 0
    - predicted_labels length must equal point count
    - confidence_scores length must equal point count
    - confidence values must be in [0.0, 1.0]
    - class IDs must be in [0, 7]
    - empty point clouds raise MappingValidationError

    Args:
        payload: Dictionary matching the perception contract.

    Returns:
        ValidatedInput with clean NumPy arrays.
    """
    if not isinstance(payload, dict):
        raise MappingValidationError(f"Expected dictionary payload, got {type(payload).__name__}")

    if "points" not in payload:
        raise MappingValidationError("Missing required field 'points' in payload")
    if "predicted_labels" not in payload:
        raise MappingValidationError("Missing required field 'predicted_labels' in payload")
    if "confidence_scores" not in payload:
        raise MappingValidationError("Missing required field 'confidence_scores' in payload")

    frame_id = str(payload.get("frame_id", "frame_0000"))

    # 1. Parse and validate points
    raw_points = payload["points"]
    if isinstance(raw_points, np.ndarray):
        points = raw_points.astype(np.float32)
    elif isinstance(raw_points, (list, tuple)):
        if len(raw_points) == 0:
            raise MappingValidationError("Empty point cloud: point count must be greater than 0")
        try:
            points = np.asarray(raw_points, dtype=np.float32)
        except Exception as e:
            raise MappingValidationError(f"Could not convert points list to array: {e}")
    else:
        raise MappingValidationError(f"Unsupported points type: {type(raw_points).__name__}")

    if points.ndim != 2 or points.shape[1] not in (3, 4):
        raise MappingValidationError(
            f"Point cloud must have shape (N, 3) or (N, 4), got {points.shape}"
        )

    num_points = points.shape[0]
    if num_points == 0:
        raise MappingValidationError("Empty point cloud: point count must be greater than 0")

    # 2. Parse and validate predicted labels
    raw_labels = payload["predicted_labels"]
    if isinstance(raw_labels, np.ndarray):
        labels = raw_labels.astype(np.int64)
    elif isinstance(raw_labels, (list, tuple)):
        labels = np.asarray(raw_labels, dtype=np.int64)
    else:
        raise MappingValidationError(f"Unsupported predicted_labels type: {type(raw_labels).__name__}")

    if labels.ndim != 1 or len(labels) != num_points:
        raise MappingValidationError(
            f"predicted_labels length ({len(labels)}) must match point count ({num_points})"
        )

    if np.any(labels < 0) or np.any(labels >= NUM_CLASSES):
        invalid_ids = labels[(labels < 0) | (labels >= NUM_CLASSES)]
        raise MappingValidationError(
            f"Class IDs must be within [0, {NUM_CLASSES - 1}], found invalid IDs: {np.unique(invalid_ids)[:5]}"
        )

    # 3. Parse and validate confidence scores
    raw_conf = payload["confidence_scores"]
    if isinstance(raw_conf, np.ndarray):
        confidences = raw_conf.astype(np.float32)
    elif isinstance(raw_conf, (list, tuple)):
        confidences = np.asarray(raw_conf, dtype=np.float32)
    else:
        raise MappingValidationError(f"Unsupported confidence_scores type: {type(raw_conf).__name__}")

    if confidences.ndim != 1 or len(confidences) != num_points:
        raise MappingValidationError(
            f"confidence_scores length ({len(confidences)}) must match point count ({num_points})"
        )

    # Allow small numerical epsilon for float rounding (e.g. 1.0000001)
    if np.any(confidences < -1e-5) or np.any(confidences > 1.0 + 1e-5):
        min_c = float(np.min(confidences))
        max_c = float(np.max(confidences))
        raise MappingValidationError(
            f"Confidence values must be in [0.0, 1.0], found range [{min_c:.4f}, {max_c:.4f}]"
        )
    confidences = np.clip(confidences, 0.0, 1.0)

    # 4. Optional ground truth labels
    gt_labels = None
    if "ground_truth_labels" in payload and payload["ground_truth_labels"] is not None:
        raw_gt = payload["ground_truth_labels"]
        gt_arr = np.asarray(raw_gt, dtype=np.int64)
        if len(gt_arr) == num_points:
            gt_labels = gt_arr

    # 5. Optional intensity
    intensity = None
    if "intensity" in payload and payload["intensity"] is not None:
        raw_int = payload["intensity"]
        int_arr = np.asarray(raw_int, dtype=np.float32)
        if len(int_arr) == num_points:
            intensity = int_arr
    elif points.shape[1] == 4:
        intensity = points[:, 3]

    return ValidatedInput(
        points=points,
        predicted_labels=labels,
        confidence_scores=confidences,
        frame_id=frame_id,
        ground_truth_labels=gt_labels,
        intensity=intensity,
    )
