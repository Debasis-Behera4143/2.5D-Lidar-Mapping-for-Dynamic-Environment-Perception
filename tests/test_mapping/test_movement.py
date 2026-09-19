"""
Unit tests for frame-to-frame movement estimation.

Verifies zero displacement for identical point clouds, measurable displacement
for translated points, graceful handling of missing previous frames, and moving ratio bounds.
"""

import numpy as np
import pytest
from src.mapping.config import MovementConfig
from src.mapping.movement import estimate_movement


class TestMovement:
    """Test suite for nearest-neighbor movement estimation."""

    def test_identical_frames_produce_zero_displacement(self):
        # 100 random points
        np.random.seed(42)
        curr = np.random.uniform(-20.0, 20.0, size=(100, 3)).astype(np.float32)
        prev = curr.copy()

        stats, moving_mask = estimate_movement(curr, prev, config=MovementConfig(threshold=0.25))

        assert stats["available"] is True
        assert pytest.approx(stats["mean_displacement"], abs=1e-5) == 0.0
        assert pytest.approx(stats["max_displacement"], abs=1e-5) == 0.0
        assert stats["moving_point_count"] == 0
        assert stats["moving_point_ratio"] == 0.0
        assert moving_mask is not None
        assert np.sum(moving_mask) == 0

    def test_translated_points_produce_measurable_displacement(self):
        np.random.seed(42)
        prev = np.array([
            [0.0, 0.0, 0.0],
            [5.0, 5.0, 1.0],
            [10.0, -10.0, 0.5],
        ], dtype=np.float32)

        # Shift all points by 1.0m along X
        curr = prev.copy()
        curr[:, 0] += 1.0

        stats, moving_mask = estimate_movement(curr, prev, config=MovementConfig(threshold=0.5))

        assert stats["available"] is True
        assert pytest.approx(stats["mean_displacement"], abs=1e-3) == 1.0
        assert pytest.approx(stats["max_displacement"], abs=1e-3) == 1.0
        # All 3 points moved 1.0m, which is > threshold 0.5m
        assert stats["moving_point_count"] == 3
        assert stats["moving_point_ratio"] == 1.0
        assert np.all(moving_mask)

    def test_partial_movement(self):
        prev = np.array([
            [0.0, 0.0, 0.0],  # static
            [10.0, 0.0, 0.0], # moving
        ], dtype=np.float32)

        curr = np.array([
            [0.0, 0.0, 0.0],  # stationary
            [12.0, 0.0, 0.0], # moved by 2.0m
        ], dtype=np.float32)

        stats, moving_mask = estimate_movement(curr, prev, config=MovementConfig(threshold=0.5))

        assert stats["available"] is True
        assert stats["moving_point_count"] == 1
        assert pytest.approx(stats["moving_point_ratio"], abs=1e-3) == 0.5
        assert moving_mask[0] == False
        assert moving_mask[1] == True

    def test_missing_previous_frame_graceful_handling(self):
        curr = np.ones((50, 3), dtype=np.float32)

        # previous_points is None
        stats_none, mask_none = estimate_movement(curr, None)
        assert stats_none["available"] is False
        assert stats_none["mean_displacement"] == 0.0
        assert stats_none["moving_point_count"] == 0
        assert stats_none["point_count"] == 50
        assert mask_none is None

        # previous_points is empty
        stats_empty, mask_empty = estimate_movement(curr, np.empty((0, 3)))
        assert stats_empty["available"] is False
        assert mask_empty is None
