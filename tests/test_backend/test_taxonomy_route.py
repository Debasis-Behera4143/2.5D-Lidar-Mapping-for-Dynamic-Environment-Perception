"""
Integration tests for Taxonomy and Sample route endpoints.

Verifies GET /api/v1/classes returns exactly 8 canonical classes with color mappings,
and GET /api/v1/samples returns discovered scan frames.
"""

from fastapi.testclient import TestClient
import pytest

from src.backend.app import app

client = TestClient(app)


class TestTaxonomyAndSampleRoutes:
    """Test suite for taxonomy and samples API endpoints."""

    def test_classes_endpoint_returns_eight_classes(self):
        resp = client.get("/api/v1/classes")
        assert resp.status_code == 200
        data = resp.json()

        assert data["num_classes"] == 8
        assert len(data["classes"]) == 8

        expected_classes = [
            (0, "road", 0.40),
            (1, "sidewalk", 0.20),
            (2, "building", 0.50),
            (3, "vegetation", 0.30),
            (4, "vehicle", 0.10),
            (5, "pedestrian", 0.05),
            (6, "pole_sign", 0.10),
            (7, "other", 0.40),
        ]

        classes_by_id = {c["class_id"]: c for c in data["classes"]}
        for cid, name, res in expected_classes:
            assert cid in classes_by_id
            c = classes_by_id[cid]
            assert c["name"] == name
            assert c["recommended_resolution_m"] == res
            assert "color" in c
            assert len(c["color"]["rgb_float"]) == 3
            assert len(c["color"]["rgb_uint8"]) == 3
            assert c["color"]["hex_code"].startswith("#")

    def test_samples_endpoint(self):
        resp = client.get("/api/v1/samples")
        assert resp.status_code == 200
        samples = resp.json()
        assert isinstance(samples, list)

        if len(samples) > 0:
            sample_id = samples[0]["sample_id"]
            single_resp = client.get(f"/api/v1/samples/{sample_id}")
            assert single_resp.status_code == 200
            assert single_resp.json()["sample_id"] == sample_id

        # Non-existent sample ID should return 404
        not_found_resp = client.get("/api/v1/samples/nonexistent_sample_id_999")
        assert not_found_resp.status_code == 404
