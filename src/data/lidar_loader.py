"""
SemanticKITTI LiDAR binary (.bin) file loader.

Loads Velodyne HDL-64E binary point clouds where each point is encoded
as 4 x float32 (X, Y, Z, Remission/Intensity).
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import numpy as np


class LiDARLoader:
    """
    Loader for raw LiDAR .bin point cloud files.
    """

    @staticmethod
    def load_bin(
        file_path: Union[str, Path],
        validate: bool = True,
    ) -> np.ndarray:
        """
        Load a LiDAR binary file (.bin) into a NumPy array of shape (N, 4).

        Args:
            file_path: Path to the .bin file.
            validate: If True, validates shape and finite value consistency.

        Returns:
            np.ndarray: Array of shape (N, 4) with dtype float32 (X, Y, Z, Intensity).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file size is not a multiple of 16 bytes (4 x float32).
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"LiDAR file not found: {path.resolve()}")

        # SemanticKITTI format: float32 binary values, 4 channels [x, y, z, intensity]
        raw_data = np.fromfile(str(path), dtype=np.float32)

        if raw_data.size % 4 != 0:
            raise ValueError(
                f"Corrupt or invalid .bin file: total float32 count {raw_data.size} "
                f"is not divisible by 4 (expected [x, y, z, intensity])."
            )

        points = raw_data.reshape(-1, 4)

        if validate:
            if not np.all(np.isfinite(points)):
                non_finite_count = int(np.sum(~np.isfinite(points)))
                # Provide a non-fatal warning or let preprocessing handle cleaning
                # but ensure array is returned properly

        return points

    @staticmethod
    def load_poses(
        poses_path: Union[str, Path],
    ) -> np.ndarray:
        """
        Load a SemanticKITTI poses.txt file containing 3x4 or 4x4 rigid transformation matrices.

        Args:
            poses_path: Path to poses.txt file.

        Returns:
            np.ndarray: Array of shape (F, 4, 4) with dtype float32 representing 4x4 sensor-to-world pose matrices.
        """
        path = Path(poses_path)
        if not path.is_file():
            raise FileNotFoundError(f"Poses file not found: {path.resolve()}")

        poses_raw = np.loadtxt(str(path), dtype=np.float32)
        if poses_raw.ndim == 1:
            poses_raw = poses_raw.reshape(1, -1)

        num_frames = len(poses_raw)
        poses = np.zeros((num_frames, 4, 4), dtype=np.float32)
        poses[:, 3, 3] = 1.0

        for i, row in enumerate(poses_raw):
            if len(row) == 12:
                poses[i, :3, :4] = row.reshape(3, 4)
            elif len(row) == 16:
                poses[i] = row.reshape(4, 4)
            else:
                raise ValueError(f"Invalid pose row length {len(row)}, expected 12 or 16 numbers.")

        return poses

    @staticmethod
    def compute_statistics(points: np.ndarray) -> Dict[str, Union[int, Tuple[float, float], Dict[str, float]]]:
        """
        Compute descriptive spatial statistics for a LiDAR point cloud.

        Args:
            points: (N, 4) or (N, 3) array of point coordinates and intensity.

        Returns:
            Dictionary containing:
                - "num_points": int
                - "shape": Tuple[int, ...]
                - "x_min_max": (min, max)
                - "y_min_max": (min, max)
                - "z_min_max": (min, max)
                - "intensity_min_max": (min, max) if intensity available
                - "has_nan": bool
                - "has_inf": bool
        """
        if points.ndim != 2 or points.shape[1] < 3:
            raise ValueError(f"Expected 2D array with at least 3 columns, got shape {points.shape}")

        num_points = points.shape[0]
        if num_points == 0:
            return {
                "num_points": 0,
                "shape": points.shape,
                "x_min_max": (0.0, 0.0),
                "y_min_max": (0.0, 0.0),
                "z_min_max": (0.0, 0.0),
                "has_nan": False,
                "has_inf": False,
            }

        finite_mask = np.all(np.isfinite(points[:, :3]), axis=1)
        valid_pts = points[finite_mask]

        stats: Dict[str, Union[int, Tuple[float, float], Dict[str, float]]] = {
            "num_points": int(num_points),
            "shape": tuple(points.shape),
            "has_nan": bool(np.isnan(points).any()),
            "has_inf": bool(np.isinf(points).any()),
            "valid_finite_points": int(np.sum(finite_mask)),
        }

        if len(valid_pts) > 0:
            stats["x_min_max"] = (float(np.min(valid_pts[:, 0])), float(np.max(valid_pts[:, 0])))
            stats["y_min_max"] = (float(np.min(valid_pts[:, 1])), float(np.max(valid_pts[:, 1])))
            stats["z_min_max"] = (float(np.min(valid_pts[:, 2])), float(np.max(valid_pts[:, 2])))
            if points.shape[1] >= 4:
                valid_i = points[np.isfinite(points[:, 3]), 3]
                if len(valid_i) > 0:
                    stats["intensity_min_max"] = (float(np.min(valid_i)), float(np.max(valid_i)))
                else:
                    stats["intensity_min_max"] = (0.0, 0.0)
        else:
            stats["x_min_max"] = (0.0, 0.0)
            stats["y_min_max"] = (0.0, 0.0)
            stats["z_min_max"] = (0.0, 0.0)

        return stats

    @classmethod
    def print_frame_summary(cls, file_path: Union[str, Path]) -> np.ndarray:
        """
        Load a frame, print its spatial summary, and return the points array.
        """
        path = Path(file_path)
        points = cls.load_bin(path)
        stats = cls.compute_statistics(points)

        print("=" * 60)
        print(f"LiDAR Frame Summary: {path.name}")
        print("=" * 60)
        print(f"File Path:          {path.resolve()}")
        print(f"Number of points:   {stats['num_points']:,}")
        print(f"Array Shape:        {stats['shape']}")
        print(f"X range [min, max]: [{stats['x_min_max'][0]:.2f}, {stats['x_min_max'][1]:.2f}] meters")
        print(f"Y range [min, max]: [{stats['y_min_max'][0]:.2f}, {stats['y_min_max'][1]:.2f}] meters")
        print(f"Z range [min, max]: [{stats['z_min_max'][0]:.2f}, {stats['z_min_max'][1]:.2f}] meters")
        if "intensity_min_max" in stats:
            print(f"Intensity [min, max]: [{stats['intensity_min_max'][0]:.3f}, {stats['intensity_min_max'][1]:.3f}]")
        print(f"Contains NaNs:      {stats['has_nan']}")
        print(f"Contains Infs:      {stats['has_inf']}")
        print("=" * 60)

        return points


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect a SemanticKITTI LiDAR .bin file.")
    parser.add_argument("bin_path", type=str, nargs="?", default=None, help="Path to .bin file")
    args = parser.parse_args()

    if args.bin_path:
        LiDARLoader.print_frame_summary(args.bin_path)
    else:
        # Default to checking sample if generated
        default_sample = Path("data/sample_kitti/sequences/00/velodyne/000000.bin")
        if default_sample.is_file():
            LiDARLoader.print_frame_summary(default_sample)
        else:
            print("No .bin file provided. Usage: python -m src.data.lidar_loader <path/to/frame.bin>")
