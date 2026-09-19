"""
Unit tests for SampleService dataset frame discovery and security.

Verifies sample discovery, missing directory resilience, metadata integrity,
and directory path-traversal attack prevention.
"""

from pathlib import Path
import tempfile
import pytest

from src.backend.services.sample_service import SampleService
from src.backend.utils.errors import SampleNotFoundError, SecurityError


class TestSampleService:
    """Test suite for SampleService."""

    def test_sample_discovery_on_existing_data(self):
        service = SampleService()
        samples = service.list_samples()

        assert isinstance(samples, list)
        if len(samples) > 0:
            sample = samples[0]
            assert "sample_id" in sample
            assert "frame_id" in sample
            assert "point_count" in sample
            assert "has_ground_truth" in sample
            assert "point_cloud_path" in sample
            assert sample["point_count"] >= 0

    def test_missing_directories_graceful_handling(self):
        """Service must return empty list without crashing when directories don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_root = Path(temp_dir)
            service = SampleService(
                data_root=empty_root,
                sample_dirs=[empty_root / "nonexistent_dataset_1", empty_root / "nonexistent_dataset_2"],
            )

            samples = service.list_samples()
            assert isinstance(samples, list)
            assert len(samples) == 0

    def test_get_sample_by_id_and_not_found(self):
        service = SampleService()
        samples = service.list_samples()

        if len(samples) > 0:
            sample_id = samples[0]["sample_id"]
            retrieved = service.get_sample(sample_id)
            assert retrieved["sample_id"] == sample_id
            assert retrieved["frame_id"] == samples[0]["frame_id"]

        with pytest.raises(SampleNotFoundError):
            service.get_sample("nonexistent_dataset_99_999999")

    def test_path_traversal_prevention(self):
        """Attempts to access files outside allowed root must raise SecurityError."""
        service = SampleService()

        # Path traversal with ../
        with pytest.raises(SecurityError):
            service.validate_secure_path(Path("../../Windows/System32/cmd.exe"))

        with pytest.raises(SecurityError):
            service.resolve_point_cloud_path("../../../etc/passwd")

    def test_synthetic_sample_creation_and_discovery(self):
        """Test discovery on an isolated temporary dataset structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_dir = temp_root / "test_kitti"
            seq_dir = dataset_dir / "sequences" / "01"
            velo_dir = seq_dir / "velodyne"
            label_dir = seq_dir / "labels"
            velo_dir.mkdir(parents=True)
            label_dir.mkdir(parents=True)

            # Create dummy .bin file (64 bytes = 4 points)
            bin_file = velo_dir / "000005.bin"
            bin_file.write_bytes(b"\x00" * 64)

            # Create dummy .label file (16 bytes = 4 labels)
            label_file = label_dir / "000005.label"
            label_file.write_bytes(b"\x00" * 16)

            service = SampleService(data_root=temp_root, sample_dirs=[dataset_dir])
            samples = service.list_samples()

            assert len(samples) == 1
            sample = samples[0]
            assert sample["sample_id"] == "test_kitti_01_000005"
            assert sample["point_count"] == 4
            assert sample["has_ground_truth"] is True
