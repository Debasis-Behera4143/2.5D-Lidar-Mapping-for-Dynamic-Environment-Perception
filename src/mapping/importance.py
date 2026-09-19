"""
Heuristic importance estimation for variable-resolution grid allocation.

Computes normalized multi-factor importance scores in range [0.0, 1.0] using:
- Semantic class prioritization (pedestrians and vehicles prioritized)
- Confidence uncertainty (lower confidence yields higher mapping scrutiny)
- Point density within cell
- Height variation (geometric complexity)
- Sensor proximity (closer objects receive finer detail)

NOTE: These are transparent heuristic prototype scores, NOT learned importance values.
"""

from typing import Any, Dict, Optional
import numpy as np
from src.mapping.config import ImportanceConfig


def calculate_point_importance(
    points: np.ndarray,
    labels: np.ndarray,
    confidences: np.ndarray,
    config: Optional[ImportanceConfig] = None,
) -> np.ndarray:
    """
    Calculate per-point heuristic importance scores in range [0.0, 1.0].

    Args:
        points: (N, 3) or (N, 4) coordinates [X, Y, Z, ...].
        labels: (N,) semantic class IDs in [0, 7].
        confidences: (N,) softmax probabilities in [0.0, 1.0].
        config: Optional ImportanceConfig with weight parameters.

    Returns:
        np.ndarray: (N,) float32 importance scores in [0.0, 1.0].
    """
    if config is None:
        config = ImportanceConfig()

    num_points = len(points)
    if num_points == 0:
        return np.empty((0,), dtype=np.float32)

    # 1. Semantic score lookup
    sem_lookup = np.array([config.semantic_scores.get(i, 0.1) for i in range(8)], dtype=np.float32)
    safe_labels = np.clip(labels, 0, 7)
    semantic_scores = sem_lookup[safe_labels]

    # 2. Uncertainty score: 1.0 - confidence (higher uncertainty -> higher importance)
    uncertainty_scores = 1.0 - np.clip(confidences, 0.0, 1.0)

    # 3. Proximity score: closer to sensor (0, 0) is more critical
    dist_xy = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)
    proximity_scores = np.clip(1.0 - (dist_xy / max(1.0, config.max_proximity_ref)), 0.0, 1.0)

    # Total weight
    total_weight = config.semantic_weight + config.uncertainty_weight + config.proximity_weight
    if total_weight <= 0:
        total_weight = 1.0

    raw_scores = (
        config.semantic_weight * semantic_scores
        + config.uncertainty_weight * uncertainty_scores
        + config.proximity_weight * proximity_scores
    ) / total_weight

    return np.clip(raw_scores, 0.0, 1.0).astype(np.float32)


def calculate_cell_importance(
    cell_data: Dict[str, Any],
    config: Optional[ImportanceConfig] = None,
) -> float:
    """
    Calculate per-cell heuristic importance score in range [0.0, 1.0].

    Args:
        cell_data: Dictionary containing aggregated cell statistics
                   (dominant_class, mean_confidence, point_count, height_variance,
                    center_x, center_y).
        config: Optional ImportanceConfig parameters.

    Returns:
        float: Normalized importance score in [0.0, 1.0].
    """
    if config is None:
        config = ImportanceConfig()

    # 1. Semantic component
    dom_class = int(cell_data.get("dominant_class", 7))
    s_sem = float(config.semantic_scores.get(dom_class, 0.1))

    # 2. Uncertainty component (1.0 - mean confidence)
    mean_conf = float(cell_data.get("mean_confidence", 0.5))
    s_unc = max(0.0, min(1.0, 1.0 - mean_conf))

    # 3. Density component
    pt_count = int(cell_data.get("point_count", 1))
    s_den = max(0.0, min(1.0, pt_count / max(1, config.max_density_ref)))

    # 4. Height variation component
    h_var = float(cell_data.get("height_variance", 0.0))
    s_h = max(0.0, min(1.0, np.sqrt(max(0.0, h_var)) / max(0.1, config.max_height_var_ref)))

    # 5. Proximity component
    cx = float(cell_data.get("center_x", 0.0))
    cy = float(cell_data.get("center_y", 0.0))
    dist = np.sqrt(cx ** 2 + cy ** 2)
    s_prox = max(0.0, min(1.0, 1.0 - (dist / max(1.0, config.max_proximity_ref))))

    # Weighted sum
    weights_sum = (
        config.semantic_weight
        + config.uncertainty_weight
        + config.density_weight
        + config.height_weight
        + config.proximity_weight
    )
    if weights_sum <= 0:
        weights_sum = 1.0

    raw_score = (
        config.semantic_weight * s_sem
        + config.uncertainty_weight * s_unc
        + config.density_weight * s_den
        + config.height_weight * s_h
        + config.proximity_weight * s_prox
    ) / weights_sum

    return round(float(np.clip(raw_score, 0.0, 1.0)), 4)
