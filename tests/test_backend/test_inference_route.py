"""
Integration tests for Inference route endpoint (POST /api/v1/inference).

Verifies payload validation, response formatting, and error handling with mocked service.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

from src.backend.app import app
from src.backend.utils.errors import SampleNotFoundError

client = TestClient(app)


class TestInferenceRoute:
    """Test suite for /api/v1/inference."""

    @patch("src.backend.routes.inference.inference_service.run_inference")
    def test_successful_inference_route(self, mock_run):
        mock_run.return_value = {
            "frame_id": "000000",
            "total_points": 2,
            "point_count": 2,
            "device": "cpu",
            "predicted_labels": [0, 4],
            "confidence_scores": [0.95, 0.88],
            "points": [[1.0, 2.0, 3.0, 0.5], [4.0, 5.0, 6.0, 0.6]],
            "class_distribution": {"road": 1, "vehicle": 1},
            "spatial_bounds": {
                "min_x": 1.0, "max_x": 4.0,
                "min_y": 2.0, "max_y": 5.0,
                "min_z": 3.0, "max_z": 6.0,
            },
            "confidence_information": {"mean": 0.915, "min": 0.88, "max": 0.95, "std": 0.035},
            "preview_points": [
                {
                    "x": 1.0, "y": 2.0, "z": 3.0, "intensity": 0.5,
                    "predicted_label": 0, "class_name": "road",
                    "confidence": 0.95, "ground_truth_label": None,
                },
                {
                    "x": 4.0, "y": 5.0, "z": 6.0, "intensity": 0.6,
                    "predicted_label": 4, "class_name": "vehicle",
                    "confidence": 0.88, "ground_truth_label": None,
                },
            ],
            "evaluation_information": None,
        }

        resp = client.post(
            "/api/v1/inference",
            json={
                "bin_path": "data/semantic_kitti/sequences/00/velodyne/000000.bin",
                "num_points": 4096,
                "interpolate_to_full": False,
                "preview_points_limit": 100,
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["frame_id"] == "000000"
        assert data["total_points"] == 2
        assert "confidence_information" in data

    @patch("src.backend.routes.inference.inference_service.run_inference")
    def test_inference_file_not_found(self, mock_run):
        mock_run.side_effect = SampleNotFoundError("File not found: nonexistent.bin")

        resp = client.post(
            "/api/v1/inference",
            json={"bin_path": "nonexistent.bin"},
        )

        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_inference_empty_path_validation_error(self):
        resp = client.post(
            "/api/v1/inference",
            json={"bin_path": "   "},
        )
        assert resp.status_code in (400, 422)
