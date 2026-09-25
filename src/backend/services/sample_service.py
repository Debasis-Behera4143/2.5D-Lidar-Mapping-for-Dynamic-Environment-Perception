"""
Sample discovery service for LiDAR dataset frames.

Discovers binary Velodyne point clouds (.bin) and synchronized labels (.label)
from configured dataset directories, enforces strict path-traversal prevention,
and extracts scan metadata.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import os

from src.backend.config import DATA_DIR, PROJECT_ROOT, SAMPLE_DIRS
from src.backend.utils.errors import SampleNotFoundError, SecurityError


class SampleService:
    """
    Manages LiDAR dataset sample discovery, path validation, and metadata extraction.
    """

    def __init__(self, data_root: Optional[Path] = None, sample_dirs: Optional[List[Path]] = None):
        self.data_root = (data_root or DATA_DIR).resolve()
        self.sample_dirs = sample_dirs or SAMPLE_DIRS

    def validate_secure_path(self, path: Path) -> Path:
        """
        Verify that a path is strictly contained within the allowed project data root
        to prevent directory traversal attacks (e.g. '../').

        Args:
            path: Target filesystem path.

        Returns:
            Resolved Path object if valid.

        Raises:
            SecurityError: If path resolves outside the allowed data root.
        """
        try:
            resolved = path.resolve()
        except Exception as e:
            raise SecurityError(f"Failed to resolve path '{path}': {e}")

        # Check if resolved is relative to data_root or project root
        allowed_roots = [self.data_root, PROJECT_ROOT.resolve()]
        is_safe = any(
            resolved == root or root in resolved.parents
            for root in allowed_roots
        )

        if not is_safe:
            raise SecurityError(
                f"Path traversal detected: '{path}' resolves outside allowed root '{self.data_root}'"
            )

        return resolved

    def list_samples(self) -> List[Dict[str, Any]]:
        """
        Scan configured dataset directories and discover available LiDAR frame scans.

        Returns:
            List of sample metadata dictionaries.
        """
        samples: List[Dict[str, Any]] = []

        for base_dir in self.sample_dirs:
            if not base_dir.is_dir():
                continue

            dataset_type = base_dir.name
            sequences_dir = base_dir / "sequences"
            if not sequences_dir.is_dir():
                continue

            for seq_dir in sorted(sequences_dir.iterdir()):
                if not seq_dir.is_dir():
                    continue

                seq_id = seq_dir.name
                velodyne_dir = seq_dir / "velodyne"
                labels_dir = seq_dir / "labels"

                if not velodyne_dir.is_dir():
                    continue

                for bin_file in sorted(velodyne_dir.glob("*.bin")):
                    frame_id = bin_file.stem
                    sample_id = f"{dataset_type}_{seq_id}_{frame_id}"

                    # Calculate point count from file size (4 float32 channels = 16 bytes per point)
                    file_size = bin_file.stat().st_size
                    point_count = file_size // 16 if file_size > 0 else 0

                    label_file = labels_dir / f"{frame_id}.label"
                    has_gt = label_file.is_file()

                    try:
                        label_path_str = str(label_file.relative_to(PROJECT_ROOT)).replace("\\", "/") if has_gt else None
                    except ValueError:
                        label_path_str = str(label_file).replace("\\", "/") if has_gt else None

                    try:
                        bin_path_str = str(bin_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
                    except ValueError:
                        bin_path_str = str(bin_file).replace("\\", "/")

                    # Check for poses.txt in sequence directory
                    poses_file = seq_dir / "poses.txt"
                    pose_mat = None
                    has_pose = False
                    if poses_file.is_file():
                        try:
                            from src.data.lidar_loader import LiDARLoader
                            all_poses = LiDARLoader.load_poses(poses_file)
                            frame_idx = int(frame_id)
                            if 0 <= frame_idx < len(all_poses):
                                pose_mat = all_poses[frame_idx].tolist()
                                has_pose = True
                        except Exception:
                            has_pose = False

                    sample_meta: Dict[str, Any] = {
                        "sample_id": sample_id,
                        "dataset_type": dataset_type,
                        "sequence_id": seq_id,
                        "frame_id": frame_id,
                        "point_count": int(point_count),
                        "file_size_bytes": int(file_size),
                        "has_ground_truth": has_gt,
                        "has_labels": has_gt,
                        "has_pose": has_pose,
                        "pose": pose_mat,
                        "point_cloud_path": bin_path_str,
                        "bin_path": bin_path_str,
                        "label_path": label_path_str,
                    }
                    samples.append(sample_meta)

        return samples

    def get_sample(self, sample_id: str) -> Dict[str, Any]:
        """
        Retrieve metadata for a specific sample by sample_id.

        Args:
            sample_id: Identifier formatted as '{dataset_type}_{sequence_id}_{frame_id}'

        Returns:
            Sample metadata dictionary.

        Raises:
            SampleNotFoundError: If sample does not exist.
        """
        all_samples = self.list_samples()
        for sample in all_samples:
            if sample["sample_id"] == sample_id:
                return sample

        raise SampleNotFoundError(f"LiDAR sample frame '{sample_id}' not found")

    def resolve_point_cloud_path(self, path_str: str) -> Path:
        """
        Resolve and validate a point cloud file path from client request.

        Args:
            path_str: String path provided in request.

        Returns:
            Validated Path object.

        Raises:
            SecurityError: If path attempts path traversal.
            SampleNotFoundError: If file does not exist.
        """
        p = Path(path_str)
        if not p.is_absolute():
            p = PROJECT_ROOT / p

        resolved = self.validate_secure_path(p)
        if not resolved.is_file():
            raise SampleNotFoundError(f"Point cloud file not found: {path_str}")

        return resolved
