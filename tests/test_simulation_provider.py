"""
Unit tests for SimulationDataProvider and FastAPIDataProvider.
"""

import pytest
from src.frontend.providers.simulation_provider import SimulationDataProvider
from src.frontend.providers.api_provider import FastAPIDataProvider


class TestSimulationDataProvider:
    """Test suite for deterministic simulation data provider."""

    def setup_method(self):
        self.provider = SimulationDataProvider(seed=42)

    def test_get_source_type(self):
        assert self.provider.get_source_type() == "Simulation"

    def test_check_health(self):
        health = self.provider.check_health()
        assert health["online"] is True
        assert "Simulation" in health["mode"]

    def test_get_available_frames(self):
        frames = self.provider.get_available_frames()
        assert len(frames) >= 3
        assert frames[0]["frame_id"] == "1248"

    def test_get_perception_data_structure(self):
        data = self.provider.get_perception_data("1248")
        assert data["_success"] is True
        assert data["provenance"] == "SIMULATION"
        assert len(data["points"]) > 1000
        assert len(data["predicted_labels"]) == len(data["points"])
        assert len(data["confidence_scores"]) == len(data["points"])
        assert "annotations" in data
        assert len(data["annotations"]) >= 4

    def test_get_perception_data_deterministic(self):
        d1 = self.provider.get_perception_data("1248")
        # Fresh provider with same seed
        p2 = SimulationDataProvider(seed=42)
        d2 = p2.get_perception_data("1248")
        assert d1["points"][0] == d2["points"][0]
        assert d1["total_points"] == d2["total_points"]

    def test_get_adaptive_map_structure(self):
        perc = self.provider.get_perception_data("1248")
        ada = self.provider.get_adaptive_map(perc)
        assert ada["_success"] is True
        assert ada["map_type"] == "adaptive_variable_resolution"
        assert len(ada["cells"]) > 50
        # Check cell fields
        cell = ada["cells"][0]
        assert "center_x" in cell
        assert "center_y" in cell
        assert "resolution" in cell
        assert "level" in cell
        assert "dominant_class" in cell

    def test_get_uniform_map_and_comparison(self):
        perc = self.provider.get_perception_data("1248")
        uni = self.provider.get_uniform_map(perc)
        ada = self.provider.get_adaptive_map(perc)
        comp = self.provider.get_map_comparison(uni, ada)
        assert comp["_success"] is True
        red = comp["comparison"]["cell_count_reduction_percent"]
        assert red < -50.0  # At least 50% cell reduction

    def test_get_elevation_profile(self):
        prof = self.provider.get_elevation_profile("1248")
        assert len(prof["distance_m"]) == len(prof["height_m"])
        assert max(prof["height_m"]) > 3.0  # Has terrain / overpass height

    def test_get_performance_metrics(self):
        metrics = self.provider.get_performance_metrics("1248")
        assert metrics["provenance"] == "SIMULATION"
        assert metrics["miou_percent"] == 87.0
        assert metrics["fps"] == 18.0
        assert metrics["latency_ms"] == 55.0
        assert metrics["memory_mb"] == 820.0

    def test_get_system_logs(self):
        logs = self.provider.get_system_logs("1248")
        assert len(logs) >= 5
        assert any("Loaded frame 1248" in l["msg"] for l in logs)

    def test_get_scene_objects(self):
        objs = self.provider.get_scene_objects("1248")
        assert objs["Vehicle"] == 3
        assert objs["Pedestrian"] == 2
        assert objs["Static (Pole/Sign)"] == 4


class TestFastAPIDataProviderFallback:
    """Test suite for FastAPIDataProvider fallback behaviors when offline."""

    def test_offline_fallback(self):
        provider = FastAPIDataProvider(base_url="http://127.0.0.1:9999")
        health = provider.check_health()
        assert health["online"] is False

        # Should seamlessly fall back to simulation data without crashing
        data = provider.get_perception_data("1248")
        assert data["_success"] is True
        assert "SIMULATION" in data["provenance"]
