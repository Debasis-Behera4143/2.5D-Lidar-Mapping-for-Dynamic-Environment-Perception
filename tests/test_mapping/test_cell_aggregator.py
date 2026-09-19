"""
Unit tests for CellAggregator logic.

Verifies elevation statistics, class histograms, dominant class calculation,
deterministic tie breaking (smallest class ID wins), and semantic purity.
"""

import numpy as np
import pytest
from src.mapping.cell_aggregator import CellAggregator


class TestCellAggregator:
    """Test suite for cell-level point aggregation."""

    def test_basic_aggregation(self):
        z = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        labels = np.array([0, 0, 1], dtype=np.int64)
        confidences = np.array([0.9, 0.8, 0.7], dtype=np.float32)

        res = CellAggregator.aggregate(z, labels, confidences)

        assert res["point_count"] == 3
        assert res["min_height"] == 1.0
        assert res["max_height"] == 3.0
        assert res["mean_height"] == 2.0
        assert pytest.approx(res["height_variance"], abs=1e-4) == 2.0 / 3.0
        assert res["dominant_class"] == 0
        assert res["class_histogram"] == {"0": 2, "1": 1}
        assert pytest.approx(res["mean_confidence"], abs=1e-4) == 0.8
        assert pytest.approx(res["semantic_purity"], abs=1e-4) == 2.0 / 3.0

    def test_deterministic_tie_breaking(self):
        """When multiple classes have equal counts, the smallest class ID must win."""
        z = np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32)
        # Class 4 (vehicle) has 2 points, Class 1 (sidewalk) has 2 points
        labels = np.array([4, 1, 4, 1], dtype=np.int64)
        confidences = np.array([0.9, 0.85, 0.8, 0.75], dtype=np.float32)

        res = CellAggregator.aggregate(z, labels, confidences)

        assert res["point_count"] == 4
        # 1 is smaller than 4, so class 1 must be dominant on tie
        assert res["dominant_class"] == 1
        assert pytest.approx(res["semantic_purity"], abs=1e-4) == 0.5

        # Three-way tie: class 5, 2, 0 each have 1 point
        z3 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        labels3 = np.array([5, 2, 0], dtype=np.int64)
        conf3 = np.array([0.8, 0.8, 0.8], dtype=np.float32)
        res3 = CellAggregator.aggregate(z3, labels3, conf3)
        assert res3["dominant_class"] == 0

    def test_single_point_cell(self):
        z = np.array([1.5], dtype=np.float32)
        labels = np.array([5], dtype=np.int64)  # pedestrian
        conf = np.array([0.95], dtype=np.float32)

        res = CellAggregator.aggregate(z, labels, conf)

        assert res["point_count"] == 1
        assert res["min_height"] == 1.5
        assert res["max_height"] == 1.5
        assert res["mean_height"] == 1.5
        assert res["height_variance"] == 0.0
        assert res["dominant_class"] == 5
        assert res["semantic_purity"] == 1.0
        assert res["mean_confidence"] == 0.95

    def test_empty_points_rejection(self):
        with pytest.raises(ValueError):
            CellAggregator.aggregate([], [], [])

    def test_mismatched_lengths_rejection(self):
        with pytest.raises(ValueError):
            CellAggregator.aggregate([1.0, 2.0], [0], [0.8, 0.9])
