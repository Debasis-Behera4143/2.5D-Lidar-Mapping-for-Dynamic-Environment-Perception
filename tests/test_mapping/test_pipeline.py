"""
Unit tests for end-to-end mapping pipeline and Member 2 integration service.

Verifies end-to-end processing, frame ID preservation, pure JSON serializability,
robust error validation on malformed inputs, and MappingService adapter functionality.
"""

import json
import numpy as np
import pytest

from src.backend.services.mapping_service import MappingService
from src.mapping.config import PipelineConfig
from src.mapping.pipeline import (
    compare_maps,
    generate_adaptive_map,
    generate_uniform_map,
    process_frame,
)
from src.mapping.types import MappingValidationError


@pytest.fixture
def sample_payload():
    """Generates a valid deterministic perception payload for testing."""
    np.random.seed(42)
    n = 100
    points = np.column_stack([
        np.random.uniform(-15.0, 15.0, n),
        np.random.uniform(-15.0, 15.0, n),
        np.random.uniform(-2.0, 2.0, n),
        np.random.uniform(0.1, 0.9, n),  # intensity
    ]).astype(np.float32)

    labels = np.random.choice([0, 1, 2, 4, 5], size=n).astype(np.int64)
    confidences = np.random.uniform(0.7, 0.99, size=n).astype(np.float32)

    return {
        "points": points,
        "predicted_labels": labels,
        "confidence_scores": confidences,
        "frame_id": "000042",
    }


class TestPipeline:
    """Test suite for pipeline functions and integration adapter."""

    def test_process_frame_end_to_end(self, sample_payload):
        res = process_frame(sample_payload)

        assert res["frame_id"] == "000042"
        assert "uniform_map" in res
        assert "adaptive_map" in res
        assert "metrics" in res
        assert "importance_summary" in res
        assert "movement" in res

        # Check subfields
        assert res["uniform_map"]["map_type"] == "uniform"
        assert res["adaptive_map"]["map_type"] == "adaptive"
        assert res["movement"]["available"] is False  # no previous frame
        assert res["metrics"]["comparison"]["cell_count_reduction_percent"] is not None

        # Verify pure JSON serializability
        json_str = json.dumps(res)
        deserialized = json.loads(json_str)
        assert deserialized["frame_id"] == "000042"

    def test_process_frame_with_previous_frame(self, sample_payload):
        # Create translated previous frame
        prev_payload = dict(sample_payload)
        prev_points = sample_payload["points"].copy()
        prev_points[:, 0] -= 1.0  # shifted
        prev_payload["points"] = prev_points
        prev_payload["frame_id"] = "000041"

        res = process_frame(sample_payload, previous_payload=prev_payload)

        assert res["movement"]["available"] is True
        assert res["movement"]["mean_displacement"] > 0.0

    def test_standalone_api_methods(self, sample_payload):
        uni = generate_uniform_map(sample_payload)
        assert uni["map_type"] == "uniform"

        ada = generate_adaptive_map(sample_payload)
        assert ada["map_type"] == "adaptive"

        comp = compare_maps(uni, ada)
        assert "comparison" in comp

    def test_mapping_service_adapter(self, sample_payload):
        service = MappingService()

        uni = service.generate_uniform_map(sample_payload, resolution=0.5)
        assert uni["resolution"] == 0.5

        ada = service.generate_adaptive_map(sample_payload, base_resolution=1.0, fine_resolution=0.25)
        assert ada["base_resolution"] == 1.0

        full_res = service.process_frame(sample_payload)
        assert full_res["frame_id"] == "000042"

    def test_invalid_payload_rejection(self):
        # Missing required field
        with pytest.raises(MappingValidationError):
            process_frame({"points": [[0, 0, 0]]})

        # Empty point cloud
        with pytest.raises(MappingValidationError):
            process_frame({
                "points": [],
                "predicted_labels": [],
                "confidence_scores": [],
                "frame_id": "000",
            })

        # Mismatched length
        with pytest.raises(MappingValidationError):
            process_frame({
                "points": [[0, 0, 0], [1, 1, 1]],
                "predicted_labels": [0],
                "confidence_scores": [0.9, 0.9],
                "frame_id": "000",
            })

        # Invalid class ID (> 7)
        with pytest.raises(MappingValidationError):
            process_frame({
                "points": [[0, 0, 0]],
                "predicted_labels": [10],
                "confidence_scores": [0.9],
                "frame_id": "000",
            })

        # Invalid confidence (> 1.0)
        with pytest.raises(MappingValidationError):
            process_frame({
                "points": [[0, 0, 0]],
                "predicted_labels": [0],
                "confidence_scores": [1.5],
                "frame_id": "000",
            })
