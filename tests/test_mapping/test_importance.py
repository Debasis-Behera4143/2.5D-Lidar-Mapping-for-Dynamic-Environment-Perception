"""
Unit tests for heuristic importance estimation.

Verifies score normalization to [0, 1], prioritization of pedestrians/vehicles over road,
uncertainty scaling, and custom weight configuration.
"""

import numpy as np
import pytest
from src.mapping.config import ImportanceConfig
from src.mapping.importance import calculate_cell_importance, calculate_point_importance


class TestImportance:
    """Test suite for point-level and cell-level importance scoring."""

    def test_point_importance_range_and_semantic_hierarchy(self):
        # Points at equal distance and equal confidence
        points = np.array([
            [10.0, 0.0, 0.0],  # pedestrian (class 5)
            [10.0, 0.0, 0.0],  # vehicle (class 4)
            [10.0, 0.0, 0.0],  # road (class 0)
            [10.0, 0.0, 0.0],  # other (class 7)
        ], dtype=np.float32)
        labels = np.array([5, 4, 0, 7], dtype=np.int64)
        confidences = np.array([0.9, 0.9, 0.9, 0.9], dtype=np.float32)

        scores = calculate_point_importance(points, labels, confidences)

        # 1. Scores must be within [0, 1]
        assert np.all(scores >= 0.0)
        assert np.all(scores <= 1.0)

        # 2. Pedestrians and vehicles must have higher default importance than road
        ped_score = scores[0]
        veh_score = scores[1]
        road_score = scores[2]
        other_score = scores[3]

        assert ped_score > road_score
        assert veh_score > road_score
        assert ped_score >= veh_score
        assert road_score > other_score

    def test_uncertainty_increases_importance(self):
        # Two pedestrian points at same location, one confident, one uncertain
        points = np.array([
            [10.0, 10.0, 0.0],
            [10.0, 10.0, 0.0],
        ], dtype=np.float32)
        labels = np.array([5, 5], dtype=np.int64)
        confidences = np.array([0.95, 0.20], dtype=np.float32)  # 2nd is uncertain

        scores = calculate_point_importance(points, labels, confidences)

        # Uncertain point should have strictly higher importance
        assert scores[1] > scores[0]

    def test_configurable_weights(self):
        # Custom config where road is boosted and semantic weight dominates
        custom_cfg = ImportanceConfig(
            semantic_weight=1.0,
            uncertainty_weight=0.0,
            proximity_weight=0.0,
            semantic_scores={0: 0.99, 5: 0.01},
        )
        points = np.array([[5.0, 5.0, 0.0], [5.0, 5.0, 0.0]], dtype=np.float32)
        labels = np.array([0, 5], dtype=np.int64)
        confidences = np.array([0.9, 0.9], dtype=np.float32)

        scores = calculate_point_importance(points, labels, confidences, config=custom_cfg)

        assert scores[0] > scores[1]
        assert pytest.approx(scores[0], abs=1e-3) == 0.99
        assert pytest.approx(scores[1], abs=1e-3) == 0.01

    def test_cell_importance_range_and_hierarchy(self):
        ped_cell = {
            "dominant_class": 5,
            "mean_confidence": 0.85,
            "point_count": 25,
            "height_variance": 0.5,
            "center_x": 5.0,
            "center_y": 5.0,
        }
        road_cell = {
            "dominant_class": 0,
            "mean_confidence": 0.95,
            "point_count": 10,
            "height_variance": 0.01,
            "center_x": 30.0,
            "center_y": 30.0,
        }

        imp_ped = calculate_cell_importance(ped_cell)
        imp_road = calculate_cell_importance(road_cell)

        assert 0.0 <= imp_ped <= 1.0
        assert 0.0 <= imp_road <= 1.0
        assert imp_ped > imp_road
