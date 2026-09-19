"""
2.5D Uniform Grid Mapper implementation.

Discretizes LiDAR point clouds into a uniform Cartesian grid using stable
floor-based cell indexing and computes elevation statistics and dominant semantics.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np

from src.mapping.cell_aggregator import CellAggregator
from src.mapping.config import UniformGridConfig


class UniformGridMapper:
    """
    Constructs a 2.5D uniform elevation and semantic occupancy grid map from LiDAR points.
    """

    def __init__(self, config: Optional[UniformGridConfig] = None):
        self.config = config if config is not None else UniformGridConfig()
        if self.config.resolution <= 0:
            raise ValueError(f"Resolution must be strictly positive (> 0), got {self.config.resolution}")

    def map_points(
        self,
        points: np.ndarray,
        labels: np.ndarray,
        confidences: np.ndarray,
        resolution: Optional[float] = None,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a uniform 2.5D grid map from points.

        Args:
            points: (N, 3) or (N, 4) point coordinates [X, Y, Z, ...].
            labels: (N,) class IDs in [0, 7].
            confidences: (N,) confidence scores in [0.0, 1.0].
            resolution: Optional override for cell resolution in meters.
            roi_bounds: Optional (min_x, max_x, min_y, max_y, [min_z, max_z]) ROI crop.

        Returns:
            Dict containing map_type, resolution, cell_count, cells, bounds, point_count.
        """
        res = float(resolution) if resolution is not None else float(self.config.resolution)
        if res <= 0:
            raise ValueError(f"Grid resolution must be strictly positive (> 0), got {res}")

        num_points = len(points)
        if num_points == 0:
            return {
                "map_type": "uniform",
                "resolution": round(res, 4),
                "cell_count": 0,
                "cells": [],
                "bounds": {"min_x": 0.0, "max_x": 0.0, "min_y": 0.0, "max_y": 0.0, "min_z": 0.0, "max_z": 0.0},
                "point_count": 0,
            }

        pts = np.asarray(points, dtype=np.float32)
        lbls = np.asarray(labels, dtype=np.int64)
        confs = np.asarray(confidences, dtype=np.float32)

        # Apply ROI filtering if provided
        active_roi = roi_bounds if roi_bounds is not None else self.config.roi_bounds
        if active_roi is not None:
            mask = (pts[:, 0] >= active_roi[0]) & (pts[:, 0] <= active_roi[1]) & \
                   (pts[:, 1] >= active_roi[2]) & (pts[:, 1] <= active_roi[3])
            if len(active_roi) >= 6:
                mask &= (pts[:, 2] >= active_roi[4]) & (pts[:, 2] <= active_roi[5])
            pts = pts[mask]
            lbls = lbls[mask]
            confs = confs[mask]

        filtered_count = len(pts)
        if filtered_count == 0:
            return {
                "map_type": "uniform",
                "resolution": round(res, 4),
                "cell_count": 0,
                "cells": [],
                "bounds": {"min_x": 0.0, "max_x": 0.0, "min_y": 0.0, "max_y": 0.0, "min_z": 0.0, "max_z": 0.0},
                "point_count": 0,
            }

        ox = float(self.config.origin_x)
        oy = float(self.config.origin_y)

        # Stable floor-based cell indexing
        gx = np.floor((pts[:, 0] - ox) / res).astype(np.int64)
        gy = np.floor((pts[:, 1] - oy) / res).astype(np.int64)

        # Group indices by (grid_x, grid_y)
        cell_groups: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for idx in range(filtered_count):
            cell_groups[(int(gx[idx]), int(gy[idx]))].append(idx)

        cells: List[Dict[str, Any]] = []
        for (grid_x, grid_y), indices in cell_groups.items():
            idx_arr = np.asarray(indices, dtype=np.int64)
            agg = CellAggregator.aggregate(pts[idx_arr, 2], lbls[idx_arr], confs[idx_arr])

            cx = round(float(ox + (grid_x + 0.5) * res), 4)
            cy = round(float(oy + (grid_y + 0.5) * res), 4)

            cell_dict: Dict[str, Any] = {
                "grid_x": int(grid_x),
                "grid_y": int(grid_y),
                "center_x": cx,
                "center_y": cy,
                "resolution": round(res, 4),
                "point_count": int(agg["point_count"]),
                "min_height": agg["min_height"],
                "max_height": agg["max_height"],
                "mean_height": agg["mean_height"],
                "height_variance": agg["height_variance"],
                "dominant_class": int(agg["dominant_class"]),
                "class_histogram": agg["class_histogram"],
                "mean_confidence": agg["mean_confidence"],
            }
            cells.append(cell_dict)

        # Sort cells deterministically by (grid_x, grid_y)
        cells.sort(key=lambda c: (c["grid_x"], c["grid_y"]))

        bounds = {
            "min_x": round(float(np.min(pts[:, 0])), 4),
            "max_x": round(float(np.max(pts[:, 0])), 4),
            "min_y": round(float(np.min(pts[:, 1])), 4),
            "max_y": round(float(np.max(pts[:, 1])), 4),
            "min_z": round(float(np.min(pts[:, 2])), 4),
            "max_z": round(float(np.max(pts[:, 2])), 4),
        }

        return {
            "map_type": "uniform",
            "resolution": round(res, 4),
            "cell_count": int(len(cells)),
            "cells": cells,
            "bounds": bounds,
            "point_count": int(filtered_count),
        }
