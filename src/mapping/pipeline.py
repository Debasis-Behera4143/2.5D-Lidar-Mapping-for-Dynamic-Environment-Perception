"""
End-to-end 2.5D LiDAR Mapping Pipeline orchestration.

Provides top-level APIs for generating uniform maps, adaptive variable-resolution maps,
movement analysis, and quantitative map comparison metrics.
"""

import time
from typing import Any, Dict, Optional
import numpy as np

from src.mapping.adaptive_mapper import AdaptiveGridMapper
from src.mapping.config import (
    AdaptiveConfig,
    ImportanceConfig,
    MovementConfig,
    PipelineConfig,
    UniformGridConfig,
)
from src.mapping.grid_mapper import UniformGridMapper
from src.mapping.importance import calculate_point_importance
from src.mapping.metrics import compare_maps as calc_compare_maps
from src.mapping.movement import estimate_movement
from src.mapping.serialization import to_json_serializable
from src.mapping.types import validate_input_payload


def generate_uniform_map(
    payload: Dict[str, Any],
    config: Optional[UniformGridConfig] = None,
) -> Dict[str, Any]:
    """
    Generate a 2.5D uniform grid map from perception output.

    Args:
        payload: Perception output dictionary containing points, predicted_labels,
                 confidence_scores, frame_id.
        config: Optional UniformGridConfig.

    Returns:
        JSON-serializable uniform map dictionary.
    """
    if config is None:
        config = UniformGridConfig()

    val_input = validate_input_payload(payload)
    mapper = UniformGridMapper(config)
    result = mapper.map_points(
        val_input.points,
        val_input.predicted_labels,
        val_input.confidence_scores,
    )
    return to_json_serializable(result)


def generate_adaptive_map(
    payload: Dict[str, Any],
    previous_payload: Optional[Dict[str, Any]] = None,
    config: Optional[AdaptiveConfig] = None,
    importance_config: Optional[ImportanceConfig] = None,
    movement_config: Optional[MovementConfig] = None,
) -> Dict[str, Any]:
    """
    Generate a 2.5D adaptive variable-resolution grid map from perception output.

    Args:
        payload: Perception output dictionary for current frame.
        previous_payload: Optional perception output for preceding frame to estimate movement.
        config: Optional AdaptiveConfig.
        importance_config: Optional ImportanceConfig.
        movement_config: Optional MovementConfig.

    Returns:
        JSON-serializable adaptive map dictionary.
    """
    if config is None:
        config = AdaptiveConfig()
    if importance_config is None:
        importance_config = ImportanceConfig()
    if movement_config is None:
        movement_config = MovementConfig()

    val_curr = validate_input_payload(payload)
    val_prev = validate_input_payload(previous_payload) if previous_payload else None

    # Estimate movement if previous frame exists
    moving_mask = None
    if val_prev is not None:
        _, moving_mask = estimate_movement(
            val_curr.points,
            val_prev.points,
            val_curr.predicted_labels,
            val_prev.predicted_labels,
            movement_config,
            current_pose=val_curr.pose,
            previous_pose=val_prev.pose,
        )

    mapper = AdaptiveGridMapper(config, importance_config)
    result = mapper.map_points(
        val_curr.points,
        val_curr.predicted_labels,
        val_curr.confidence_scores,
        moving_mask=moving_mask,
    )
    return to_json_serializable(result)


def compare_maps(
    uniform_map: Dict[str, Any],
    adaptive_map: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute quantitative comparison metrics between uniform and adaptive maps.

    Args:
        uniform_map: Uniform map dictionary.
        adaptive_map: Adaptive map dictionary.

    Returns:
        JSON-serializable comparison dictionary.
    """
    metrics = calc_compare_maps(uniform_map, adaptive_map)
    return to_json_serializable(metrics)


def process_frame(
    payload: Dict[str, Any],
    previous_payload: Optional[Dict[str, Any]] = None,
    config: Optional[PipelineConfig] = None,
) -> Dict[str, Any]:
    """
    Execute full end-to-end mapping pipeline on a LiDAR frame:
    1. Validate input payload contracts.
    2. Calculate point-level heuristic importance.
    3. Calculate frame-to-frame movement (if previous frame is available).
    4. Generate uniform 2.5D grid map.
    5. Generate adaptive variable-resolution 2.5D grid map.
    6. Calculate comparative efficiency metrics.
    7. Return pure JSON-serializable result.

    Args:
        payload: Current frame perception output dictionary.
        previous_payload: Optional previous frame perception output dictionary.
        config: Optional PipelineConfig.

    Returns:
        JSON-serializable dictionary with keys:
        frame_id, uniform_map, adaptive_map, metrics, importance_summary, movement.
    """
    if config is None:
        config = PipelineConfig()

    val_curr = validate_input_payload(payload)
    val_prev = validate_input_payload(previous_payload) if previous_payload is not None else None

    # 1. Point-level importance scoring
    pt_importance = calculate_point_importance(
        val_curr.points,
        val_curr.predicted_labels,
        val_curr.confidence_scores,
        config.importance,
    )
    if len(pt_importance) > 0:
        importance_summary = {
            "mean": round(float(np.mean(pt_importance)), 4),
            "min": round(float(np.min(pt_importance)), 4),
            "max": round(float(np.max(pt_importance)), 4),
            "std": round(float(np.std(pt_importance)), 4),
        }
    else:
        importance_summary = {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

    # 2. Movement estimation
    movement_stats, moving_mask = estimate_movement(
        val_curr.points,
        val_prev.points if val_prev is not None else None,
        val_curr.predicted_labels,
        val_prev.predicted_labels if val_prev is not None else None,
        config.movement,
        current_pose=val_curr.pose if val_curr is not None else None,
        previous_pose=val_prev.pose if val_prev is not None else None,
    )

    # 3. Uniform grid mapping
    t0 = time.perf_counter()
    uni_mapper = UniformGridMapper(config.uniform)
    uniform_map = uni_mapper.map_points(
        val_curr.points,
        val_curr.predicted_labels,
        val_curr.confidence_scores,
    )
    uni_time = time.perf_counter() - t0

    # 4. Adaptive variable-resolution mapping
    t1 = time.perf_counter()
    ada_mapper = AdaptiveGridMapper(config.adaptive, config.importance)
    adaptive_map = ada_mapper.map_points(
        val_curr.points,
        val_curr.predicted_labels,
        val_curr.confidence_scores,
        moving_mask=moving_mask,
    )
    ada_time = time.perf_counter() - t1

    # 5. Comparative benchmark metrics
    metrics = calc_compare_maps(
        uniform_map,
        adaptive_map,
        uniform_time_s=uni_time,
        adaptive_time_s=ada_time,
    )

    output: Dict[str, Any] = {
        "frame_id": val_curr.frame_id,
        "uniform_map": uniform_map,
        "adaptive_map": adaptive_map,
        "metrics": metrics,
        "importance_summary": importance_summary,
        "movement": movement_stats,
    }

    return to_json_serializable(output)
