"""
Unit tests for mapping metrics and comparative benchmarks.

Verifies percentage reduction computations, finiteness of calculations,
sparsity, and graceful handling of empty/edge cases.
"""

import math
import pytest
from src.mapping.metrics import compare_maps, compute_map_summary


class TestMetrics:
    """Test suite for map summary and comparative metrics."""

    def test_basic_map_summary(self):
        map_dict = {
            "map_type": "uniform",
            "resolution": 0.5,
            "cell_count": 4,
            "point_count": 20,
            "cells": [
                {"resolution": 0.5, "point_count": 5, "level": "coarse"},
                {"resolution": 0.5, "point_count": 5, "level": "coarse"},
                {"resolution": 0.5, "point_count": 5, "level": "coarse"},
                {"resolution": 0.5, "point_count": 5, "level": "coarse"},
            ],
            "bounds": {"min_x": 0.0, "max_x": 2.0, "min_y": 0.0, "max_y": 2.0, "min_z": 0.0, "max_z": 1.0},
        }

        summary = compute_map_summary(map_dict, execution_time_s=0.01)

        assert summary["cell_count"] == 4
        assert summary["point_count"] == 20
        # 4 cells * 0.25 m2 = 1.0 m2
        assert summary["occupied_area_m2"] == 1.0
        assert summary["avg_points_per_cell"] == 5.0
        # Bounds area = 2.0 * 2.0 = 4.0 m2. Sparsity = 1 - 1/4 = 0.75
        assert pytest.approx(summary["map_sparsity"], abs=1e-3) == 0.75
        # 4 * 64 bytes = 256 bytes
        assert summary["estimated_memory_bytes"] == 256
        assert summary["execution_time_ms"] == 10.0

    def test_compare_maps_reduction_percentages(self):
        # Uniform map with 100 cells
        uniform_map = {
            "map_type": "uniform",
            "resolution": 0.25,
            "cell_count": 100,
            "point_count": 500,
            "cells": [{"resolution": 0.25, "point_count": 5, "level": "fine"} for _ in range(100)],
            "bounds": {"min_x": 0.0, "max_x": 10.0, "min_y": 0.0, "max_y": 10.0},
        }
        # Adaptive map with 40 cells (60% reduction)
        adaptive_map = {
            "map_type": "adaptive",
            "base_resolution": 1.0,
            "fine_resolution": 0.25,
            "cell_count": 40,
            "coarse_cell_count": 20,
            "fine_cell_count": 20,
            "point_count": 500,
            "cells": (
                [{"resolution": 1.0, "point_count": 15, "level": "coarse"} for _ in range(20)]
                + [{"resolution": 0.25, "point_count": 10, "level": "fine"} for _ in range(20)]
            ),
            "bounds": {"min_x": 0.0, "max_x": 10.0, "min_y": 0.0, "max_y": 10.0},
        }

        res = compare_maps(uniform_map, adaptive_map)

        comp = res["comparison"]
        # (100 - 40) / 100 * 100 = 60.0%
        assert pytest.approx(comp["cell_count_reduction_percent"], abs=1e-2) == 60.0
        assert pytest.approx(comp["estimated_memory_reduction_percent"], abs=1e-2) == 60.0
        assert math.isfinite(comp["cell_count_reduction_percent"])
        assert math.isfinite(comp["estimated_memory_reduction_percent"])
        assert "methodology_note" in comp

    def test_empty_maps_comparison_safety(self):
        empty_map = {
            "map_type": "uniform",
            "resolution": 0.5,
            "cell_count": 0,
            "point_count": 0,
            "cells": [],
            "bounds": {},
        }
        res = compare_maps(empty_map, empty_map)

        assert res["comparison"]["cell_count_reduction_percent"] == 0.0
        assert res["comparison"]["estimated_memory_reduction_percent"] == 0.0
        assert math.isfinite(res["comparison"]["cell_count_reduction_percent"])
