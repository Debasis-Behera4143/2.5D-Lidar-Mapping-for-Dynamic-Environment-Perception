"""
Unit tests for Backend Pydantic V2 Data Schemas.

Verifies:
- Valid request and response creation
- Rejection of invalid negative or zero values
- Rejection of invalid ROI bounds (min >= max)
- Rejection of out-of-range confidence scores (< 0.0 or > 1.0)
- Rejection of out-of-range percentages (< 0.0 or > 100.0)
- Rejection of invalid class IDs (< 0 or > 7)
- Rejection of empty/whitespace paths
- JSON serializability without NumPy types
- Taxonomy integrity: exactly 8 classes with correct resolutions and color palettes
"""

import json
import pytest
from pydantic import ValidationError

from src.backend.schemas.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    ROIBounds,
    SpatialBounds,
    SuccessResponse,
)
from src.backend.schemas.health import (
    CheckpointStatus,
    CudaStatus,
    DeviceInfo,
    HealthResponse,
)
from src.backend.schemas.inference import (
    ConfidenceSummary,
    InferenceEvaluationInfo,
    InferenceRequest,
    InferenceResponse,
    PointPreviewItem,
)
from src.backend.schemas.mapping import (
    GridCellPreview,
    MappingRequest,
    MappingResponse,
    MemoryEstimate,
)
from src.backend.schemas.metrics import MetricsResponse
from src.backend.schemas.sample import (
    SampleItem,
    SampleListResponse,
)
from src.backend.schemas.taxonomy import (
    PROJECT_TAXONOMY_ITEMS,
    PROJECT_TAXONOMY_MAP,
    ClassTaxonomyItem,
    ColorInfo,
    TaxonomyResponse,
    get_class_taxonomy,
    get_taxonomy_response,
)


class TestRequestCreation:
    """Verify valid instantiation and default values for request schemas."""

    def test_valid_inference_request_defaults(self):
        req = InferenceRequest(bin_path="data/semantic_kitti/sequences/00/velodyne/000000.bin")
        assert req.bin_path == "data/semantic_kitti/sequences/00/velodyne/000000.bin"
        assert req.label_path is None
        assert req.num_points == 4096
        assert req.interpolate_to_full is False
        assert req.preview_points_limit == 2000

    def test_valid_inference_request_custom(self):
        req = InferenceRequest(
            bin_path="data/test.bin",
            label_path="data/test.label",
            num_points=8192,
            interpolate_to_full=True,
            preview_points_limit=500,
        )
        assert req.num_points == 8192
        assert req.interpolate_to_full is True
        assert req.preview_points_limit == 500

    def test_valid_mapping_request_defaults(self):
        req = MappingRequest(bin_path="data/test.bin")
        assert req.bin_path == "data/test.bin"
        assert req.coarse_resolution == 0.40
        assert req.fine_resolution == 0.10
        assert req.pedestrian_resolution == 0.05
        assert req.interpolate_to_full is True
        assert req.roi_bounds.min_x == -40.0
        assert req.roi_bounds.max_x == 40.0

    def test_valid_mapping_request_with_tuple_roi(self):
        req = MappingRequest(
            bin_path="data/test.bin",
            roi_bounds=(-30.0, 30.0, -25.0, 25.0, -2.0, 3.5),
            coarse_resolution=0.50,
            fine_resolution=0.15,
            pedestrian_resolution=0.08,
        )
        assert req.roi_bounds.min_x == -30.0
        assert req.roi_bounds.max_x == 30.0
        assert req.roi_bounds.min_z == -2.0
        assert req.roi_bounds.max_z == 3.5
        assert req.coarse_resolution == 0.50

    def test_valid_sample_item(self):
        sample = SampleItem(
            dataset_type="semantic_kitti",
            sequence_id="00",
            frame_id="000000",
            bin_path="data/semantic_kitti/sequences/00/velodyne/000000.bin",
            label_path="data/semantic_kitti/sequences/00/labels/000000.label",
            file_size_bytes=1900000,
            point_count=120000,
            has_labels=True,
        )
        assert sample.sequence_id == "00"
        assert sample.point_count == 120000
        assert sample.has_labels is True

    def test_valid_health_response(self):
        health = HealthResponse(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.5,
            device_info=DeviceInfo(
                device_type="cpu",
                device_name="Intel Core i7",
                torch_version="2.0.1",
                python_version="3.10.12",
            ),
            cuda_status=CudaStatus(
                is_available=False,
                device_count=0,
            ),
            checkpoint_status=CheckpointStatus(
                checkpoint_path="checkpoints/best_randlanet.pt",
                exists=True,
                size_bytes=50000000,
                is_loaded=True,
            ),
        )
        assert health.status == "healthy"
        assert health.device_info.device_type == "cpu"
        assert health.cuda_status.is_available is False


class TestNegativeAndZeroValidation:
    """Verify validation errors for negative or non-positive values where positive is required."""

    def test_negative_or_zero_points_in_inference_request(self):
        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="scan.bin", num_points=0)

        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="scan.bin", num_points=-10)

    def test_negative_or_zero_preview_limit(self):
        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="scan.bin", preview_points_limit=0)

        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="scan.bin", preview_points_limit=-5)

    def test_negative_or_zero_resolutions_in_mapping_request(self):
        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", coarse_resolution=0.0)

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", coarse_resolution=-0.4)

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", fine_resolution=0.0)

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", fine_resolution=-0.1)

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", pedestrian_resolution=0.0)

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", pedestrian_resolution=-0.05)

    def test_negative_or_zero_sample_metrics(self):
        with pytest.raises(ValidationError):
            SampleItem(
                dataset_type="kitti",
                sequence_id="00",
                frame_id="000",
                bin_path="a.bin",
                file_size_bytes=0,
                point_count=1000,
            )

        with pytest.raises(ValidationError):
            SampleItem(
                dataset_type="kitti",
                sequence_id="00",
                frame_id="000",
                bin_path="a.bin",
                file_size_bytes=1000,
                point_count=-1,
            )


class TestROIBoundsValidation:
    """Verify ROI and SpatialBounds validation rules (min < max)."""

    def test_valid_bounds(self):
        bounds = SpatialBounds(
            min_x=-10.0, max_x=10.0,
            min_y=-20.0, max_y=20.0,
            min_z=-2.0, max_z=3.0,
        )
        assert bounds.to_tuple() == (-10.0, 10.0, -20.0, 20.0, -2.0, 3.0)

    def test_invalid_x_bounds(self):
        with pytest.raises(ValidationError):
            SpatialBounds(
                min_x=10.0, max_x=-10.0,
                min_y=-5.0, max_y=5.0,
                min_z=-1.0, max_z=1.0,
            )
        with pytest.raises(ValidationError):
            SpatialBounds(
                min_x=10.0, max_x=10.0,  # equal
                min_y=-5.0, max_y=5.0,
                min_z=-1.0, max_z=1.0,
            )

    def test_invalid_y_bounds(self):
        with pytest.raises(ValidationError):
            SpatialBounds(
                min_x=-10.0, max_x=10.0,
                min_y=15.0, max_y=5.0,
                min_z=-1.0, max_z=1.0,
            )

    def test_invalid_z_bounds(self):
        with pytest.raises(ValidationError):
            SpatialBounds(
                min_x=-10.0, max_x=10.0,
                min_y=-5.0, max_y=5.0,
                min_z=2.0, max_z=1.0,
            )

    def test_invalid_roi_tuple_length(self):
        with pytest.raises(ValueError):
            ROIBounds.from_tuple((-10.0, 10.0, -5.0))

        with pytest.raises(ValidationError):
            ROIBounds.model_validate((-10.0, 10.0, -5.0))

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="scan.bin", roi_bounds=(-10.0, 10.0))


class TestConfidenceAndPercentageValidation:
    """Verify confidence values in [0, 1] and percentage values in [0, 100]."""

    def test_invalid_confidence_scores(self):
        with pytest.raises(ValidationError):
            ConfidenceSummary(mean=1.2, min=0.1, max=0.9)

        with pytest.raises(ValidationError):
            ConfidenceSummary(mean=-0.1, min=0.0, max=0.8)

        with pytest.raises(ValidationError):
            PointPreviewItem(
                x=1.0, y=2.0, z=0.0, intensity=0.5,
                predicted_label=0, class_name="road",
                confidence=1.05,
            )

        with pytest.raises(ValidationError):
            PointPreviewItem(
                x=1.0, y=2.0, z=0.0, intensity=0.5,
                predicted_label=0, class_name="road",
                confidence=-0.01,
            )

    def test_invalid_percentage_bounds(self):
        with pytest.raises(ValidationError):
            InferenceEvaluationInfo(
                accuracy_percent=105.0,
                evaluated_points=1000,
            )

        with pytest.raises(ValidationError):
            InferenceEvaluationInfo(
                accuracy_percent=-5.0,
                evaluated_points=1000,
            )

        with pytest.raises(ValidationError):
            MetricsResponse(
                device="cpu",
                inference_latency=0.15,
                throughput=1000.0,
                accuracy=101.0,
            )

        with pytest.raises(ValidationError):
            MetricsResponse(
                device="cpu",
                inference_latency=0.15,
                throughput=1000.0,
                mIoU=-1.0,
            )


class TestClassIDAndPathValidation:
    """Verify class IDs are within [0, 7] and file paths cannot be blank."""

    def test_invalid_class_ids(self):
        with pytest.raises(ValidationError):
            ClassTaxonomyItem(
                class_id=-1,
                name="invalid",
                priority="None",
                color=ColorInfo(rgb_float=[0, 0, 0], rgb_uint8=[0, 0, 0], hex_code="#000000"),
                recommended_resolution_m=0.1,
            )

        with pytest.raises(ValidationError):
            ClassTaxonomyItem(
                class_id=8,
                name="invalid",
                priority="None",
                color=ColorInfo(rgb_float=[0, 0, 0], rgb_uint8=[0, 0, 0], hex_code="#000000"),
                recommended_resolution_m=0.1,
            )

        with pytest.raises(ValidationError):
            PointPreviewItem(
                x=0.0, y=0.0, z=0.0, intensity=0.0,
                predicted_label=10,
                class_name="out_of_bounds",
                confidence=0.5,
            )

    def test_empty_or_whitespace_paths(self):
        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="")

        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="   ")

        with pytest.raises(ValidationError):
            InferenceRequest(bin_path="valid.bin", label_path="   ")

        with pytest.raises(ValidationError):
            MappingRequest(bin_path="")

        with pytest.raises(ValidationError):
            SampleItem(
                dataset_type="kitti",
                sequence_id="00",
                frame_id="000",
                bin_path="   ",
                file_size_bytes=100,
                point_count=100,
            )


class TestTaxonomyIntegrity:
    """Verify taxonomy structure, exactly 8 classes, and resolution recommendations."""

    def test_taxonomy_has_exactly_eight_classes(self):
        taxonomy = get_taxonomy_response()
        assert taxonomy.num_classes == 8
        assert len(taxonomy.classes) == 8
        assert len(PROJECT_TAXONOMY_ITEMS) == 8

    def test_taxonomy_classes_and_ids(self):
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

        for exp_id, exp_name, exp_res in expected_classes:
            item = get_class_taxonomy(exp_id)
            assert item.class_id == exp_id
            assert item.name == exp_name
            assert item.recommended_resolution_m == exp_res
            assert len(item.color.rgb_float) == 3
            assert len(item.color.rgb_uint8) == 3
            assert item.color.hex_code.startswith("#")


class TestResponseSerialization:
    """Verify JSON serializability of all response schemas using pure Python primitives."""

    def test_inference_response_serialization(self):
        resp = InferenceResponse(
            frame_id="000000",
            total_points=4096,
            predicted_labels=[0, 1, 4, 5, 6, 7],
            confidence_information=ConfidenceSummary(
                mean=0.88,
                min=0.45,
                max=0.99,
                std=0.08,
            ),
            class_distribution={"road": 3000, "vehicle": 1096},
            spatial_bounds=SpatialBounds(
                min_x=-30.0, max_x=30.0,
                min_y=-20.0, max_y=20.0,
                min_z=-2.0, max_z=3.0,
            ),
            preview_points=[
                PointPreviewItem(
                    x=5.2, y=1.4, z=-0.5, intensity=0.3,
                    predicted_label=4, class_name="vehicle",
                    confidence=0.95,
                    ground_truth_label=4,
                ),
                PointPreviewItem(
                    x=2.1, y=-1.0, z=-1.7, intensity=0.1,
                    predicted_label=0, class_name="road",
                    confidence=0.99,
                ),
            ],
            evaluation_information=InferenceEvaluationInfo(
                accuracy_percent=92.5,
                mean_iou_percent=78.2,
                evaluated_points=4096,
                per_class_iou={"road": 95.0, "vehicle": 85.2},
            ),
        )

        dumped = resp.model_dump()
        json_str = resp.model_dump_json()
        deserialized = json.loads(json_str)

        assert deserialized["frame_id"] == "000000"
        assert deserialized["total_points"] == 4096
        assert len(deserialized["preview_points"]) == 2
        assert deserialized["evaluation_information"]["accuracy_percent"] == 92.5
        # Re-parse from JSON string
        reparsed = InferenceResponse.model_validate_json(json_str)
        assert reparsed.total_points == 4096

    def test_mapping_response_serialization(self):
        resp = MappingResponse(
            frame_id="000000",
            status="completed",
            grid_type="adaptive_variable_resolution_2.5d",
            execution_time=0.042,
            total_input_points=120000,
            allocated_cells=8540,
            memory_estimate=MemoryEstimate(
                estimated_bytes=1048576,
                estimated_mb=1.0,
                formatted="1.00 MB",
            ),
            resolution_breakdown={
                "coarse_0.40m": 6000,
                "fine_0.10m": 2000,
                "pedestrian_0.05m": 540,
            },
            map_bounds=SpatialBounds(
                min_x=-40.0, max_x=40.0,
                min_y=-40.0, max_y=40.0,
                min_z=-3.0, max_z=4.0,
            ),
            preview_grid_cells=[
                GridCellPreview(
                    center_x=10.0,
                    center_y=-5.0,
                    resolution=0.10,
                    elevation_min=-1.7,
                    elevation_max=-0.5,
                    dominant_class_id=4,
                    dominant_class_name="vehicle",
                    point_count=45,
                    occupancy=0.92,
                ),
            ],
        )

        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["allocated_cells"] == 8540
        assert parsed["memory_estimate"]["formatted"] == "1.00 MB"
        assert parsed["preview_grid_cells"][0]["dominant_class_name"] == "vehicle"

    def test_metrics_response_serialization(self):
        metrics = MetricsResponse(
            model_name="RandLA-Net",
            device="cpu",
            number_of_classes=8,
            inference_latency=0.085,
            throughput=48188.0,
            accuracy=2.5,
            mIoU=5.7,
            prototype_status="baseline_prototype_1_epoch",
            limitation_note="Baseline prototype disclosure note",
        )
        json_str = metrics.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["accuracy"] == 2.5
        assert parsed["mIoU"] == 5.7
        assert parsed["number_of_classes"] == 8
