"""
Unit tests for AdaptiveGridMapper.

Verifies dual coarse/fine resolution generation, prioritization of high-importance
regions with finer resolution, exactly-once point accounting, and non-overlapping cells.
"""

import numpy as np
import pytest
from src.mapping.adaptive_mapper import AdaptiveGridMapper
from src.mapping.config import AdaptiveConfig, ImportanceConfig


class TestAdaptiveGridMapper:
    """Test suite for coarse-to-fine adaptive 2.5D grid mapping."""

    def test_coarse_and_fine_cell_generation(self):
        # Create a scene with:
        # 1. Low-importance road points at X in [0, 1], Y in [0, 1]
        # 2. High-importance pedestrian points at X in [10, 11], Y in [10, 11]
        np.random.seed(42)
        n_road = 30
        road_pts = np.column_stack([
            np.random.uniform(0.1, 0.9, n_road),
            np.random.uniform(0.1, 0.9, n_road),
            np.random.uniform(-1.7, -1.6, n_road),
        ]).astype(np.float32)
        road_lbls = np.zeros(n_road, dtype=np.int64)  # class 0: road
        road_confs = np.full(n_road, 0.95, dtype=np.float32)

        n_ped = 30
        ped_pts = np.column_stack([
            np.random.uniform(10.1, 10.9, n_ped),
            np.random.uniform(10.1, 10.9, n_ped),
            np.random.uniform(0.0, 1.5, n_ped),
        ]).astype(np.float32)
        ped_lbls = np.full(n_ped, 5, dtype=np.int64)  # class 5: pedestrian
        ped_confs = np.full(n_ped, 0.90, dtype=np.float32)

        points = np.vstack([road_pts, ped_pts])
        labels = np.concatenate([road_lbls, ped_lbls])
        confidences = np.concatenate([road_confs, ped_confs])

        cfg = AdaptiveConfig(
            base_resolution=1.0,
            fine_resolution=0.25,
            importance_threshold=0.45,
        )
        mapper = AdaptiveGridMapper(cfg)
        res = mapper.map_points(points, labels, confidences)

        assert res["map_type"] == "adaptive"
        assert res["point_count"] == 60
        assert res["coarse_cell_count"] > 0
        assert res["fine_cell_count"] > 0
        assert res["cell_count"] == res["coarse_cell_count"] + res["fine_cell_count"]

        # Exactly-once point representation check:
        # Sum of point counts in all cells must equal total input points
        cell_points_sum = sum(c["point_count"] for c in res["cells"])
        assert cell_points_sum == 60

        # Verify resolution levels
        coarse_cells = [c for c in res["cells"] if c["level"] == "coarse"]
        fine_cells = [c for c in res["cells"] if c["level"] == "fine"]

        assert len(coarse_cells) == res["coarse_cell_count"]
        assert len(fine_cells) == res["fine_cell_count"]

        # All coarse cells must have resolution 1.0
        for c in coarse_cells:
            assert c["resolution"] == 1.0
            assert c["dominant_class"] == 0  # road

        # All fine cells must have resolution 0.25
        for c in fine_cells:
            assert c["resolution"] == 0.25
            assert c["dominant_class"] == 5  # pedestrian

    def test_dynamic_points_trigger_subdivision(self):
        # Road points, but moving mask marks them dynamic
        points = np.array([
            [0.1, 0.1, 0.0],
            [0.2, 0.8, 0.0],
            [0.8, 0.2, 0.0],
            [0.9, 0.9, 0.0],
        ], dtype=np.float32)
        labels = np.zeros(4, dtype=np.int64)  # road (low static importance)
        confidences = np.full(4, 0.95, dtype=np.float32)
        moving_mask = np.array([True, True, True, True])

        cfg = AdaptiveConfig(
            base_resolution=1.0,
            fine_resolution=0.5,
            importance_threshold=0.8,  # high threshold
            dynamic_threshold=0.25,
        )
        mapper = AdaptiveGridMapper(cfg)
        res = mapper.map_points(points, labels, confidences, moving_mask=moving_mask)

        # Dynamic flag must force fine resolution
        assert res["fine_cell_count"] > 0
        assert res["coarse_cell_count"] == 0
        assert all(c["is_dynamic"] for c in res["cells"])

    def test_no_overlapping_duplicate_cells(self):
        """Ensure no two cells share overlapping coordinates or represent duplicated points."""
        np.random.seed(123)
        n = 150
        pts = np.random.uniform(-10.0, 10.0, size=(n, 3)).astype(np.float32)
        lbls = np.random.choice([0, 1, 4, 5], size=n)
        confs = np.random.uniform(0.7, 1.0, size=n).astype(np.float32)

        mapper = AdaptiveGridMapper(AdaptiveConfig(base_resolution=2.0, fine_resolution=0.5))
        res = mapper.map_points(pts, lbls, confs)

        # Invariant 1: Total points preserved
        assert sum(c["point_count"] for c in res["cells"]) == n

        # Invariant 2: Unique cell centers
        centers = [(c["center_x"], c["center_y"], c["resolution"]) for c in res["cells"]]
        assert len(centers) == len(set(centers))

    def test_invalid_resolution_rejection(self):
        with pytest.raises(ValueError):
            AdaptiveConfig(base_resolution=0.5, fine_resolution=1.0)  # fine >= base

        with pytest.raises(ValueError):
            AdaptiveConfig(base_resolution=-1.0, fine_resolution=0.5)

        with pytest.raises(ValueError):
            AdaptiveConfig(base_resolution=1.0, fine_resolution=-0.5)
