"""
Frontend data adapter and visualization processing utilities.

Manages:
- Safe visualization-only downsampling (maintains mapping integrity)
- Cell extraction and formatting for 2D/3D rendering
- Geometric candidate cluster estimation for object analysis
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.cluster import DBSCAN

from src.frontend.config import (
    CLASS_COLORS,
    CLASS_NAMES,
    DEFAULT_BASE_RESOLUTION,
    DEFAULT_DYNAMIC_THRESHOLD,
    DEFAULT_FINE_RESOLUTION,
    DEFAULT_IMPORTANCE_THRESHOLD,
    DEFAULT_NUM_POINTS,
    DEFAULT_PREVIEW_POINTS,
)


def get_preview_points(
    perception_dict: Dict[str, Any],
    max_points: int = DEFAULT_PREVIEW_POINTS,
    selected_classes: Optional[List[int]] = None,
    min_confidence: float = 0.0,
) -> Dict[str, Any]:
    """
    Filter and downsample points specifically for WebGL/3D visualization.
    Never alters original perception data used by mapping.

    Returns:
        dict with filtered (x, y, z, intensity, labels, confidences, colors, class_names).
    """
    if not perception_dict or "points" not in perception_dict:
        return {}

    raw_pts = np.asarray(perception_dict["points"], dtype=np.float32)
    labels = np.asarray(perception_dict.get("predicted_labels", []), dtype=np.int64)
    confs = np.asarray(perception_dict.get("confidence_scores", []), dtype=np.float32)

    total = len(raw_pts)
    if total == 0:
        return {}

    if len(labels) != total or len(confs) != total:
        return {}

    # Filtering mask
    mask = confs >= min_confidence
    if selected_classes is not None and len(selected_classes) > 0:
        mask = mask & np.isin(labels, selected_classes)

    pts_filtered = raw_pts[mask]
    lbls_filtered = labels[mask]
    confs_filtered = confs[mask]

    n_filtered = len(pts_filtered)
    if n_filtered == 0:
        return {
            "x": [], "y": [], "z": [], "intensity": [],
            "labels": [], "confidences": [], "colors": [],
            "class_names": [], "total_points": total, "visible_points": 0,
        }

    # Strided downsampling for fast 60fps rendering
    if n_filtered > max_points:
        indices = np.linspace(0, n_filtered - 1, max_points, dtype=int)
        pts_view = pts_filtered[indices]
        lbls_view = lbls_filtered[indices]
        confs_view = confs_filtered[indices]
    else:
        pts_view = pts_filtered
        lbls_view = lbls_filtered
        confs_view = confs_filtered

    colors = [CLASS_COLORS.get(int(lbl), "#a5a5a5") for lbl in lbls_view]
    class_names = [CLASS_NAMES.get(int(lbl), f"class_{lbl}") for lbl in lbls_view]
    intensity = pts_view[:, 3] if pts_view.shape[1] > 3 else np.zeros(len(pts_view))

    return {
        "x": pts_view[:, 0],
        "y": pts_view[:, 1],
        "z": pts_view[:, 2],
        "intensity": intensity,
        "labels": lbls_view,
        "confidences": confs_view,
        "colors": colors,
        "class_names": class_names,
        "total_points": total,
        "visible_points": len(pts_view),
    }


def extract_candidate_clusters(
    points: np.ndarray,
    labels: np.ndarray,
    target_classes: Optional[List[int]] = None,
    eps: float = 0.8,
    min_samples: int = 5,
) -> List[Dict[str, Any]]:
    """
    Extract spatial candidate 3D clusters (e.g. for vehicles and pedestrians)
    using DBSCAN spatial clustering on semantic points.

    Returns:
        List of cluster bounding box dictionaries:
        {
            'cluster_id': int,
            'class_id': int,
            'class_name': str,
            'point_count': int,
            'center': [x, y, z],
            'min_bound': [x, y, z],
            'max_bound': [x, y, z],
            'dims': [dx, dy, dz]
        }
    """
    if len(points) == 0:
        return []

    # Default target classes: vehicles (4), pedestrians (5), pole_sign (6)
    if target_classes is None:
        target_classes = [4, 5, 6]

    mask = np.isin(labels, target_classes)
    obj_points = points[mask]
    obj_labels = labels[mask]

    if len(obj_points) < min_samples:
        return []

    clusters: List[Dict[str, Any]] = []
    cluster_counter = 0

    for cls_id in target_classes:
        cls_mask = (obj_labels == cls_id)
        cls_pts = obj_points[cls_mask]
        if len(cls_pts) < min_samples:
            continue

        # Cluster on XY horizontal coordinates
        db = DBSCAN(eps=eps, min_samples=min_samples)
        db_labels = db.fit_predict(cls_pts[:, :3])

        for c_id in np.unique(db_labels):
            if c_id == -1:
                continue  # Skip noise
            c_mask = (db_labels == c_id)
            c_pts = cls_pts[c_mask]

            min_b = np.min(c_pts[:, :3], axis=0)
            max_b = np.max(c_pts[:, :3], axis=0)
            center = np.mean(c_pts[:, :3], axis=0)
            dims = max_b - min_b

            # Filter unrealistic huge clusters
            if dims[0] > 12.0 or dims[1] > 12.0 or dims[2] > 6.0:
                continue

            clusters.append({
                "cluster_id": cluster_counter,
                "class_id": cls_id,
                "class_name": CLASS_NAMES.get(cls_id, f"class_{cls_id}"),
                "point_count": int(len(c_pts)),
                "center": [round(float(c), 3) for c in center],
                "min_bound": [round(float(b), 3) for b in min_b],
                "max_bound": [round(float(b), 3) for b in max_b],
                "dims": [round(float(d), 3) for d in dims],
            })
            cluster_counter += 1

    return clusters
