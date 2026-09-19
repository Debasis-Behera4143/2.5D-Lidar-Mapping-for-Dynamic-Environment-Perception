"""
Frame-to-frame geometric movement estimation.

Estimates local spatial displacements between sequential LiDAR point cloud frames
using nearest-neighbor distance metrics via scipy.spatial.cKDTree.

NOTE: This is a fast geometric nearest-neighbor heuristic prototype, NOT full 3D
scene-flow tracking or ego-motion compensated SLAM.
"""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from src.mapping.config import MovementConfig

try:
    from scipy.spatial import cKDTree
    HAS_CKDTREE = True
except ImportError:
    HAS_CKDTREE = False


def estimate_movement(
    current_points: np.ndarray,
    previous_points: Optional[np.ndarray] = None,
    current_labels: Optional[np.ndarray] = None,
    previous_labels: Optional[np.ndarray] = None,
    config: Optional[MovementConfig] = None,
) -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
    """
    Estimate displacement and moving point ratio between two consecutive LiDAR frames.

    Args:
        current_points: (N, 3) or (N, 4) coordinates of current frame.
        previous_points: Optional (M, 3) or (M, 4) coordinates of previous frame.
        current_labels: Optional (N,) class IDs for current points.
        previous_labels: Optional (M,) class IDs for previous points.
        config: Optional MovementConfig specifying threshold and radius parameters.

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
        }, None

    curr_xyz = np.asarray(current_points[:, :3], dtype=np.float32)
    prev_xyz = np.asarray(previous_points[:, :3], dtype=np.float32)

    if HAS_CKDTREE:
        tree = cKDTree(prev_xyz)
        distances, _ = tree.query(curr_xyz, k=1, distance_upper_bound=config.max_search_radius)
        # cKDTree returns inf for points beyond distance_upper_bound
        inf_mask = np.isinf(distances)
        if np.any(inf_mask):
            distances[inf_mask] = config.max_search_radius
    else:
        # Fallback for small point clouds if scipy is missing
        # Compute min Euclidean distance per point in chunks to prevent memory explosion
        distances = np.zeros(num_curr, dtype=np.float32)
        chunk_size = 500
        for i in range(0, num_curr, chunk_size):
            chunk = curr_xyz[i:i + chunk_size]
            diff = chunk[:, np.newaxis, :] - prev_xyz[np.newaxis, :, :]
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
    }

    return movement_stats, moving_mask
