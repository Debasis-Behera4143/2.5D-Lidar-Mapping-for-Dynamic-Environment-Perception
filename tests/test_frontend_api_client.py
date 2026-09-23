"""
Unit and Integration Tests for Frontend ApiClient and Data Adapter.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from src.frontend.api_client import ApiClient
from src.frontend.config import CANONICAL_TAXONOMY, CLASS_COLORS, CLASS_NAMES
from src.frontend.data_adapter import extract_candidate_clusters, get_preview_points


class TestApiClient:
    """Test suite for Frontend ApiClient."""

    @patch("httpx.Client.get")
    def test_check_health_online(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "healthy",
            "version": "1.0.0",
            "device_info": {"device_name": "CPU"},
            "checkpoint_status": {"exists": True},
        }
        mock_get.return_value = mock_resp

        client = ApiClient(base_url="http://127.0.0.1:8000")
        health = client.check_health()

        assert health["online"] is True
        assert health["status"] == "healthy"
        assert health["ping_ms"] is not None

    @patch("httpx.Client.get")
    def test_check_health_offline_connect_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        client = ApiClient(base_url="http://127.0.0.1:8000")
        health = client.check_health()

        assert health["online"] is False
        assert health["status"] == "offline"
        assert "could not be reached" in health["error"]

    @patch("httpx.Client.get")
    def test_get_classes_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"num_classes": 8, "classes": CANONICAL_TAXONOMY}
        mock_get.return_value = mock_resp

        client = ApiClient()
        classes = client.get_classes()

        assert len(classes) == 8
        assert classes[0]["name"] == "road"

    @patch("httpx.Client.post")
    def test_run_inference_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "frame_id": "000000",
            "total_points": 4096,
            "predicted_labels": [0] * 4096,
            "confidence_scores": [0.9] * 4096,
            "points": [[1.0, 2.0, 0.0, 0.5]] * 4096,
            "class_distribution": {"road": 4096},
        }
        mock_post.return_value = mock_resp

        client = ApiClient()
        resp = client.run_inference(bin_path="dummy.bin")

        assert resp["_success"] is True
        assert resp["total_points"] == 4096
        assert len(resp["points"]) == 4096

    @patch("httpx.Client.post")
    def test_run_inference_failure(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"detail": "File not found"}
        mock_post.return_value = mock_resp

        client = ApiClient()
        resp = client.run_inference(bin_path="nonexistent.bin")

        assert resp["_success"] is False
        assert "not found" in resp["error"].lower()


class TestDataAdapter:
    """Test suite for Data Adapter and Downsampling Utilities."""

    def test_get_preview_points_filtering(self):
        pts = np.array([
            [1.0, 2.0, 0.5, 0.2],
            [3.0, 4.0, 1.0, 0.8],
            [5.0, 6.0, 2.0, 0.5],
        ], dtype=np.float32)
        lbls = np.array([0, 4, 5], dtype=np.int64)  # road, vehicle, pedestrian
        confs = np.array([0.9, 0.7, 0.4], dtype=np.float32)

        perc = {
            "points": pts,
            "predicted_labels": lbls,
            "confidence_scores": confs,
        }

        # Filter: confidence >= 0.5 and class in [4, 5]
        res = get_preview_points(
            perc,
            max_points=100,
            selected_classes=[4, 5],
            min_confidence=0.5,
        )

        assert res["total_points"] == 3
        assert res["visible_points"] == 1  # Only index 1 (vehicle, conf 0.7) passes
        assert res["labels"][0] == 4

    def test_extract_candidate_clusters(self):
        # 10 vehicle points clustered around (10, 10, 0)
        pts_veh = np.random.uniform(9.5, 10.5, size=(10, 4)).astype(np.float32)
        pts_veh[:, 2] = np.random.uniform(-0.5, 0.5, size=10)
        lbls_veh = np.full(10, 4, dtype=np.int64)  # vehicle class 4

        clusters = extract_candidate_clusters(pts_veh, lbls_veh, target_classes=[4], eps=1.5, min_samples=3)

        assert len(clusters) == 1
        assert clusters[0]["class_id"] == 4
        assert clusters[0]["class_name"] == "vehicle"
        assert clusters[0]["point_count"] == 10
