"""
Adaptive Variable-Resolution 2.5D Grid Mapper implementation.

Executes a coarse-to-fine variable resolution strategy:
- Evaluates base-resolution cells with heuristic importance and movement metrics
- Preserves low-importance static regions at coarse base resolution
- Subdivides high-importance or dynamic regions into fine resolution cells
- Guarantees non-overlapping cells and exact 1:1 point representation
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np

from src.mapping.cell_aggregator import CellAggregator
from src.mapping.config import AdaptiveConfig, ImportanceConfig
from src.mapping.importance import calculate_cell_importance


class AdaptiveGridMapper:
    """
    Constructs an adaptive variable-resolution 2.5D elevation and semantic grid map.
    """

    def __init__(
        self,
        config: Optional[AdaptiveConfig] = None,
        importance_config: Optional[ImportanceConfig] = None,
    ):
        self.config = config if config is not None else AdaptiveConfig()
        self.importance_config = importance_config if importance_config is not None else ImportanceConfig()

    def map_points(
        self,
        points: np.ndarray,
        labels: np.ndarray,
        confidences: np.ndarray,
        moving_mask: Optional[np.ndarray] = None,
        base_resolution: Optional[float] = None,
        fine_resolution: Optional[float] = None,
        importance_threshold: Optional[float] = None,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an adaptive 2.5D grid map.

        Args:
            points: (N, 3) or (N, 4) point coordinates [X, Y, Z, ...].
            labels: (N,) class IDs in [0, 7].
            confidences: (N,) confidence scores in [0.0, 1.0].
            moving_mask: Optional (N,) boolean mask indicating moving points.
            base_resolution: Optional coarse base resolution override in meters.
            fine_resolution: Optional fine resolution override in meters.
            importance_threshold: Optional importance cutoff override.
            roi_bounds: Optional ROI crop box.

        Returns:
            Dict containing map_type, base_resolution, fine_resolution, cell_count,
            coarse_cell_count, fine_cell_count, cells, bounds, point_count.
        """
        base_res = float(base_resolution) if base_resolution is not None else float(self.config.base_resolution)
        fine_res = float(fine_resolution) if fine_resolution is not None else float(self.config.fine_resolution)
        imp_thresh = float(importance_threshold) if importance_threshold is not None else float(self.config.importance_threshold)

        if base_res <= 0:
            raise ValueError(f"base_resolution must be strictly positive (> 0), got {base_res}")
        if fine_res <= 0:
            raise ValueError(f"fine_resolution must be strictly positive (> 0), got {fine_res}")
        if fine_res >= base_res:
            raise ValueError(f"fine_resolution ({fine_res}) must be smaller than base_resolution ({base_res})")

        num_points = len(points)
        if num_points == 0:
            return {
                "map_type": "adaptive",
                "base_resolution": round(base_res, 4),
                "fine_resolution": round(fine_res, 4),
                "cell_count": 0,
                "coarse_cell_count": 0,
                "fine_cell_count": 0,
                "cells": [],
                "bounds": {"min_x": 0.0, "max_x": 0.0, "min_y": 0.0, "max_y": 0.0, "min_z": 0.0, "max_z": 0.0},
                "point_count": 0,
            }

        pts = np.asarray(points, dtype=np.float32)
        lbls = np.asarray(labels, dtype=np.int64)
        confs = np.asarray(confidences, dtype=np.float32)
        m_mask = np.asarray(moving_mask, dtype=bool) if moving_mask is not None else None

        # ROI filtering
        active_roi = roi_bounds if roi_bounds is not None else self.config.roi_bounds
        if active_roi is not None:
            mask = (pts[:, 0] >= active_roi[0]) & (pts[:, 0] <= active_roi[1]) & \
                   (pts[:, 1] >= active_roi[2]) & (pts[:, 1] <= active_roi[3])
            if len(active_roi) >= 6:
                mask &= (pts[:, 2] >= active_roi[4]) & (pts[:, 2] <= active_roi[5])
            pts = pts[mask]
            lbls = lbls[mask]
            confs = confs[mask]
            if m_mask is not None:
                m_mask = m_mask[mask]

        filtered_count = len(pts)
        if filtered_count == 0:
            return {
                "map_type": "adaptive",
                "base_resolution": round(base_res, 4),
                "fine_resolution": round(fine_res, 4),
                "cell_count": 0,
                "coarse_cell_count": 0,
                "fine_cell_count": 0,
                "cells": [],
                "bounds": {"min_x": 0.0, "max_x": 0.0, "min_y": 0.0, "max_y": 0.0, "min_z": 0.0, "max_z": 0.0},
                "point_count": 0,
            }

        ox = float(self.config.origin_x)
        oy = float(self.config.origin_y)

        # 1. Bin points into base-resolution cells (coarse grid)
        bgx = np.floor((pts[:, 0] - ox) / base_res).astype(np.int64)
        bgy = np.floor((pts[:, 1] - oy) / base_res).astype(np.int64)

        base_groups: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for idx in range(filtered_count):
            base_groups[(int(bgx[idx]), int(bgy[idx]))].append(idx)

        final_cells: List[Dict[str, Any]] = []
        coarse_cell_count = 0
        fine_cell_count = 0

        # 2. Evaluate each coarse base cell
        for (grid_bx, grid_by), base_indices in base_groups.items():
            if len(base_indices) < self.config.min_points_per_cell:
                continue

            base_idx_arr = np.asarray(base_indices, dtype=np.int64)
            base_agg = CellAggregator.aggregate(
                pts[base_idx_arr, 2],
                lbls[base_idx_arr],
                confs[base_idx_arr],
            )

            bcx = round(float(ox + (grid_bx + 0.5) * base_res), 4)
            bcy = round(float(oy + (grid_by + 0.5) * base_res), 4)

            cell_eval_info = {
                "dominant_class": base_agg["dominant_class"],
                "mean_confidence": base_agg["mean_confidence"],
                "point_count": base_agg["point_count"],
                "height_variance": base_agg["height_variance"],
                "center_x": bcx,
                "center_y": bcy,
            }
            base_importance = calculate_cell_importance(cell_eval_info, self.importance_config)

            # Determine dynamic state
            is_dynamic = False
            if m_mask is not None:
                moving_pts = np.sum(m_mask[base_idx_arr])
                dynamic_ratio = float(moving_pts / len(base_idx_arr))
                is_dynamic = dynamic_ratio >= float(self.config.dynamic_threshold)

            # Subdivide if importance exceeds threshold or cell is dynamic
            should_subdivide = (base_importance >= imp_thresh) or is_dynamic

            if should_subdivide:
                # 3. Subdivide base cell points into fine-resolution subcells
                sub_pts = pts[base_idx_arr]
                sub_lbls = lbls[base_idx_arr]
                sub_confs = confs[base_idx_arr]

                fgx = np.floor((sub_pts[:, 0] - ox) / fine_res).astype(np.int64)
                fgy = np.floor((sub_pts[:, 1] - oy) / fine_res).astype(np.int64)

                fine_groups: Dict[Tuple[int, int], List[int]] = defaultdict(list)
                for local_i in range(len(base_idx_arr)):
                    fine_groups[(int(fgx[local_i]), int(fgy[local_i]))].append(local_i)

                for (grid_fx, grid_fy), fine_local_indices in fine_groups.items():
                    fine_local_arr = np.asarray(fine_local_indices, dtype=np.int64)
                    fine_agg = CellAggregator.aggregate(
                        sub_pts[fine_local_arr, 2],
                        sub_lbls[fine_local_arr],
                        sub_confs[fine_local_arr],
                    )

                    fcx = round(float(ox + (grid_fx + 0.5) * fine_res), 4)
                    fcy = round(float(oy + (grid_fy + 0.5) * fine_res), 4)

                    fine_eval = {
                        "dominant_class": fine_agg["dominant_class"],
                        "mean_confidence": fine_agg["mean_confidence"],
                        "point_count": fine_agg["point_count"],
                        "height_variance": fine_agg["height_variance"],
                        "center_x": fcx,
                        "center_y": fcy,
                    }
                    fine_imp = calculate_cell_importance(fine_eval, self.importance_config)

                    fine_cell = {
                        "grid_x": int(grid_fx),
                        "grid_y": int(grid_fy),
                        "center_x": fcx,
                        "center_y": fcy,
                        "resolution": round(fine_res, 4),
                        "level": "fine",
                        "point_count": int(fine_agg["point_count"]),
                        "mean_height": fine_agg["mean_height"],
                        "dominant_class": int(fine_agg["dominant_class"]),
                        "mean_confidence": fine_agg["mean_confidence"],
                        "importance_score": fine_imp,
                        "is_dynamic": bool(is_dynamic),
                    }
                    final_cells.append(fine_cell)
                    fine_cell_count += 1
            else:
                # 4. Retain coarse cell at base resolution
                coarse_cell = {
                    "grid_x": int(grid_bx),
                    "grid_y": int(grid_by),
                    "center_x": bcx,
                    "center_y": bcy,
                    "resolution": round(base_res, 4),
                    "level": "coarse",
                    "point_count": int(base_agg["point_count"]),
                    "mean_height": base_agg["mean_height"],
                    "dominant_class": int(base_agg["dominant_class"]),
                    "mean_confidence": base_agg["mean_confidence"],
                    "importance_score": base_importance,
                    "is_dynamic": bool(is_dynamic),
                }
                final_cells.append(coarse_cell)
                coarse_cell_count += 1

        # Sort cells deterministically
        final_cells.sort(key=lambda c: (c["resolution"], c["grid_x"], c["grid_y"]))

        bounds = {
            "min_x": round(float(np.min(pts[:, 0])), 4),
            "max_x": round(float(np.max(pts[:, 0])), 4),
            "min_y": round(float(np.min(pts[:, 1])), 4),
            "max_y": round(float(np.max(pts[:, 1])), 4),
            "min_z": round(float(np.min(pts[:, 2])), 4),
            "max_z": round(float(np.max(pts[:, 2])), 4),
        }

        return {
            "map_type": "adaptive",
            "base_resolution": round(base_res, 4),
            "fine_resolution": round(fine_res, 4),
            "cell_count": int(len(final_cells)),
            "coarse_cell_count": int(coarse_cell_count),
            "fine_cell_count": int(fine_cell_count),
            "cells": final_cells,
            "bounds": bounds,
            "point_count": int(filtered_count),
        }
