"""
Unit tests for UniformGridMapper.

Verifies floor-based indexing, cell bounds, elevation statistics, dominant class,
point counts, and rejection of invalid resolutions.
"""

import numpy as np
import pytest
from src.mapping.config import UniformGridConfig
from src.mapping.grid_mapper import UniformGridMapper


class TestUniformGridMapper:
    """Test suite for uniform 2.5D grid mapping."""

    def test_cell_assignment_and_floor_indexing(self):
        # Resolution 1.0 meter
        # Points at (0.2, 0.4) and (0.8, 0.9) belong to cell (0, 0)
        # Point at (-0.5, 0.5) belongs to cell (-1, 0)
        # Point at (1.5, 2.5) belongs to cell (1, 2)
        points = np.array([
            [0.2, 0.4, 0.1],
            [0.8, 0.9, 0.5],
            [-0.5, 0.5, 1.0],
            [1.5, 2.5, 2.0],
        ], dtype=np.float32)
        labels = np.array([0, 0, 4, 5], dtype=np.int64)
        confidences = np.array([0.9, 0.8, 0.95, 0.99], dtype=np.float32)

        mapper = UniformGridMapper(UniformGridConfig(resolution=1.0))
        res = mapper.map_points(points, labels, confidences)

        assert res["map_type"] == "uniform"
        assert res["resolution"] == 1.0
        assert res["cell_count"] == 3
        assert res["point_count"] == 4

        # Verify cells
        cells_dict = {(c["grid_x"], c["grid_y"]): c for c in res["cells"]}

        assert (0, 0) in cells_dict
        c00 = cells_dict[(0, 0)]
        assert c00["point_count"] == 2
        assert c00["center_x"] == 0.5
        assert c00["center_y"] == 0.5
        assert c00["min_height"] == 0.1
        assert c00["max_height"] == 0.5
        assert c00["dominant_class"] == 0

        assert (-1, 0) in cells_dict
        c_neg = cells_dict[(-1, 0)]
        assert c_neg["point_count"] == 1
        assert c_neg["center_x"] == -0.5
        assert c_neg["center_y"] == 0.5
        assert c_neg["dominant_class"] == 4  # vehicle

        assert (1, 2) in cells_dict
        c12 = cells_dict[(1, 2)]
        assert c12["center_x"] == 1.5
        assert c12["center_y"] == 2.5
        assert c12["dominant_class"] == 5  # pedestrian

    def test_bounds_computation(self):
        points = np.array([
            [-10.0, -20.0, -1.5],
            [15.0, 25.0, 3.2],
        ], dtype=np.float32)
        labels = np.array([0, 2], dtype=np.int64)
        confidences = np.array([0.9, 0.9], dtype=np.float32)

        mapper = UniformGridMapper(UniformGridConfig(resolution=0.5))
        res = mapper.map_points(points, labels, confidences)

        bounds = res["bounds"]
        assert bounds["min_x"] == -10.0
        assert bounds["max_x"] == 15.0
        assert bounds["min_y"] == -20.0
        assert bounds["max_y"] == 25.0
        assert bounds["min_z"] == -1.5
        assert bounds["max_z"] == 3.2

    def test_roi_clipping(self):
        points = np.array([
            [5.0, 5.0, 0.0],
            [50.0, 5.0, 0.0],   # Outside ROI
            [5.0, -50.0, 0.0],  # Outside ROI
        ], dtype=np.float32)
        labels = np.array([0, 1, 2], dtype=np.int64)
        confidences = np.array([0.9, 0.9, 0.9], dtype=np.float32)

        mapper = UniformGridMapper(UniformGridConfig(
            resolution=1.0,
            roi_bounds=(-10.0, 10.0, -10.0, 10.0),
        ))
        res = mapper.map_points(points, labels, confidences)

        assert res["point_count"] == 1
        assert res["cell_count"] == 1
        assert res["cells"][0]["grid_x"] == 5
        assert res["cells"][0]["grid_y"] == 5

    def test_invalid_resolution_rejection(self):
        with pytest.raises(ValueError):
            UniformGridConfig(resolution=0.0)

        with pytest.raises(ValueError):
            UniformGridConfig(resolution=-0.5)

        mapper = UniformGridMapper(UniformGridConfig(resolution=1.0))
        with pytest.raises(ValueError):
            mapper.map_points(np.ones((2, 3)), np.zeros(2), np.ones(2), resolution=-1.0)

    def test_empty_points_handling(self):
        mapper = UniformGridMapper(UniformGridConfig(resolution=0.5))
        res = mapper.map_points(np.empty((0, 3)), np.empty((0,)), np.empty((0,)))
        assert res["cell_count"] == 0
        assert res["point_count"] == 0
        assert res["cells"] == []
