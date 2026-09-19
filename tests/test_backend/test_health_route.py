"""
Integration tests for Health route and root endpoint.

Verifies GET /api/v1/health diagnostics and GET / service discovery using FastAPI TestClient.
"""

from fastapi.testclient import TestClient
import pytest

from src.backend.app import app

client = TestClient(app)


class TestHealthRoutes:
    """Test suite for health and root endpoints."""

    def test_root_endpoint(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "version" in data
        assert "available_endpoints" in data
        assert "/api/v1/health" in data["available_endpoints"]
        assert "/api/v1/classes" in data["available_endpoints"]

    def test_health_endpoint_structure(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "device_info" in data
        assert "cuda_status" in data
        assert "checkpoint_status" in data

        # Validate DeviceInfo sub-fields
        dev = data["device_info"]
        assert "device_type" in dev
        assert dev["device_type"] in ("cpu", "cuda")
        assert "torch_version" in dev
        assert "python_version" in dev

        # Validate CudaStatus sub-fields
        cuda = data["cuda_status"]
        assert "is_available" in cuda
        assert isinstance(cuda["is_available"], bool)
        assert "device_count" in cuda

        # Validate CheckpointStatus sub-fields
        ckpt = data["checkpoint_status"]
        assert "checkpoint_path" in ckpt
        assert "exists" in ckpt
        assert isinstance(ckpt["exists"], bool)
