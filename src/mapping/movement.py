"""
Frame-to-frame geometric movement estimation.

Estimates local spatial displacements between sequential LiDAR point cloud frames
using nearest-neighbor distance metrics via scipy.spatial.cKDTree.

Supports rigid-body ego-motion compensation when frame-to-world sensor poses are provided,
transforming sequential point clouds into a common coordinate frame before 1-NN evaluation.
"""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from src.mapping.config import MovementConfig

try:
    from scipy.spatial import cKDTree
    HAS_CKDTREE = True
except ImportError:
    HAS_CKDTREE = False


def _parse_pose(pose: Any) -> Tuple[np.ndarray, np.ndarray]:
    """Extract (3, 3) rotation matrix R and (3,) translation vector t from 3x4 or 4x4 matrix."""
    arr = np.asarray(pose, dtype=np.float32)
    if arr.shape == (3, 4):
        return arr[:3, :3], arr[:3, 3]
    elif arr.shape == (4, 4):
        return arr[:3, :3], arr[:3, 3]
    raise ValueError(f"Invalid pose matrix shape {arr.shape}, expected (3, 4) or (4, 4)")


def estimate_movement(
    current_points: np.ndarray,
    previous_points: Optional[np.ndarray] = None,
    current_labels: Optional[np.ndarray] = None,
    previous_labels: Optional[np.ndarray] = None,
    config: Optional[MovementConfig] = None,
    current_pose: Optional[np.ndarray] = None,
    previous_pose: Optional[np.ndarray] = None,
    relative_pose: Optional[np.ndarray] = None,
) -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
    """
    Estimate displacement and moving point ratio between two consecutive LiDAR frames,
    optionally compensating for ego-vehicle sensor motion using pose matrices.

    Args:
        current_points: (N, 3) or (N, 4) coordinates of current frame.
        previous_points: Optional (M, 3) or (M, 4) coordinates of previous frame.
        current_labels: Optional (N,) class IDs for current points.
        previous_labels: Optional (M,) class IDs for previous points.
        config: Optional MovementConfig specifying threshold and radius parameters.
        current_pose: Optional (4, 4) or (3, 4) sensor-to-world pose matrix for current frame.
        previous_pose: Optional (4, 4) or (3, 4) sensor-to-world pose matrix for previous frame.
        relative_pose: Optional (4, 4) or (3, 4) relative pose matrix (previous -> current).

    Returns:
        Tuple containing:
        - movement_stats: Dict matching the standard movement output contract.
        - moving_mask: (N,) boolean ndarray where True indicates a point exceeded threshold,
                       or None if previous_points was not available.
    """
    if config is None:
        config = MovementConfig()

    threshold = float(config.threshold)
    num_curr = len(current_points) if current_points is not None else 0

    # Handle missing or empty previous frame gracefully
    if previous_points is None or len(previous_points) == 0 or num_curr == 0:
        return {
            "available": False,
            "mean_displacement": 0.0,
            "max_displacement": 0.0,
            "moving_point_ratio": 0.0,
            "moving_point_count": 0,
            "point_count": int(num_curr),
            "threshold": threshold,
            "ego_compensation_applied": False,
        }, None

    curr_xyz = np.asarray(current_points[:, :3], dtype=np.float32)
    prev_xyz = np.asarray(previous_points[:, :3], dtype=np.float32)

    # Perform ego-motion compensation if enabled and poses are available
    ego_applied = False
    curr_eval_xyz = curr_xyz
    prev_eval_xyz = prev_xyz

    if config.use_ego_compensation:
        if current_pose is not None and previous_pose is not None:
            try:
                R_curr, t_curr = _parse_pose(current_pose)
                R_prev, t_prev = _parse_pose(previous_pose)
                # Transform both point clouds into common world frame: P_world = P_sensor @ R.T + t
                curr_eval_xyz = curr_xyz @ R_curr.T + t_curr
                prev_eval_xyz = prev_xyz @ R_prev.T + t_prev
                ego_applied = True
            except Exception:
                curr_eval_xyz = curr_xyz
                prev_eval_xyz = prev_xyz
        elif relative_pose is not None:
            try:
                R_rel, t_rel = _parse_pose(relative_pose)
                # Transform previous points into current sensor frame
                prev_eval_xyz = prev_xyz @ R_rel.T + t_rel
                curr_eval_xyz = curr_xyz
                ego_applied = True
            except Exception:
                curr_eval_xyz = curr_xyz
                prev_eval_xyz = prev_xyz

    if HAS_CKDTREE:
        tree = cKDTree(prev_eval_xyz)
        distances, _ = tree.query(curr_eval_xyz, k=1, distance_upper_bound=config.max_search_radius)
        # cKDTree returns inf for points beyond distance_upper_bound
        inf_mask = np.isinf(distances)
        if np.any(inf_mask):
            distances[inf_mask] = config.max_search_radius
    else:
        # Fallback for small point clouds if scipy is missing
        distances = np.zeros(num_curr, dtype=np.float32)
        chunk_size = 500
        for i in range(0, num_curr, chunk_size):
            chunk = curr_eval_xyz[i:i + chunk_size]
            diff = chunk[:, np.newaxis, :] - prev_eval_xyz[np.newaxis, :, :]
            dist_sq = np.sum(diff ** 2, axis=-1)
            distances[i:i + chunk_size] = np.sqrt(np.min(dist_sq, axis=1))

    moving_mask = distances > threshold
    moving_count = int(np.sum(moving_mask))
    moving_ratio = float(moving_count / num_curr) if num_curr > 0 else 0.0
    mean_disp = float(np.mean(distances)) if num_curr > 0 else 0.0
    max_disp = float(np.max(distances)) if num_curr > 0 else 0.0

    movement_stats: Dict[str, Any] = {
        "available": True,
        "mean_displacement": round(mean_disp, 4),
        "max_displacement": round(max_disp, 4),
        "moving_point_ratio": round(moving_ratio, 4),
        "moving_point_count": moving_count,
        "point_count": int(num_curr),
        "threshold": threshold,
        "ego_compensation_applied": ego_applied,
    }

    return movement_stats, moving_mask
