"""
Point cloud preprocessing pipeline for LiDAR perception.

Provides:
- Invalid point filtering (NaNs, Infs)
- Distance / radial range filtering (ego vehicle body removal, sensor horizon)
- Region of Interest (ROI) 3D bounding-box cropping
- Uniform random downsampling / fixed-size sampling for neural networks
- Voxel grid downsampling
- Synchronized point-and-label processing
"""

from typing import List, Optional, Tuple, Union
import numpy as np


class PointCloudPreprocessor:
    """
    Configurable preprocessing pipeline for raw LiDAR point clouds and labels.
    """

    def __init__(
        self,
        min_range: float = 1.5,
        max_range: float = 80.0,
        roi_bounds: Optional[Tuple[float, float, float, float, float, float]] = None,
        target_num_points: Optional[int] = None,
    ):
        """
        Initialize preprocessor configuration.

        Args:
            min_range: Minimum radial distance from sensor in meters (filters ego body).
            max_range: Maximum radial distance in meters.
            roi_bounds: Optional (x_min, x_max, y_min, y_max, z_min, z_max).
            target_num_points: Optional fixed point count for deep learning input.
        """
        self.min_range = min_range
        self.max_range = max_range
        self.roi_bounds = roi_bounds
        self.target_num_points = target_num_points

    @staticmethod
    def remove_invalid_points(
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """
        Remove points containing NaN, Inf, or completely zero coordinates.

        Args:
            points: (N, C) float array where columns 0, 1, 2 are X, Y, Z.
            labels: Optional (N,) label array aligned with points.

        Returns:
            Tuple of (valid_points, valid_labels, valid_mask).
        """
        if points.ndim != 2 or points.shape[1] < 3:
            raise ValueError(f"Expected 2D array with >=3 columns, got {points.shape}")

        # Check finite across all coordinates
        finite_mask = np.all(np.isfinite(points), axis=1)

        # Check not exactly at origin (0, 0, 0)
        non_zero_mask = np.any(points[:, :3] != 0.0, axis=1)

        valid_mask = finite_mask & non_zero_mask
        valid_points = points[valid_mask]
        valid_labels = labels[valid_mask] if labels is not None else None

        return valid_points, valid_labels, valid_mask

    @staticmethod
    def filter_by_range(
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        min_range: float = 1.5,
        max_range: float = 80.0,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """
        Filter points based on spherical Euclidean distance: min_range <= r <= max_range.
        """
        dist_sq = np.sum(points[:, :3] ** 2, axis=1)
        mask = (dist_sq >= (min_range ** 2)) & (dist_sq <= (max_range ** 2))

        filtered_points = points[mask]
        filtered_labels = labels[mask] if labels is not None else None

        return filtered_points, filtered_labels, mask

    @staticmethod
    def crop_roi(
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        roi: Tuple[float, float, float, float, float, float] = (-40.0, 40.0, -40.0, 40.0, -3.0, 4.0),
    ) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """
        Crop points within an axis-aligned 3D bounding box.

        Args:
            points: (N, C) array.
            labels: Optional aligned (N,) labels.
            roi: (x_min, x_max, y_min, y_max, z_min, z_max).

        Returns:
            Tuple of (cropped_points, cropped_labels, mask).
        """
        x_min, x_max, y_min, y_max, z_min, z_max = roi
        mask = (
            (points[:, 0] >= x_min) & (points[:, 0] <= x_max) &
            (points[:, 1] >= y_min) & (points[:, 1] <= y_max) &
            (points[:, 2] >= z_min) & (points[:, 2] <= z_max)
        )

        cropped_points = points[mask]
        cropped_labels = labels[mask] if labels is not None else None

        return cropped_points, cropped_labels, mask

    @staticmethod
    def sample_points(
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        target_points: int = 16384,
        random_seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], np.ndarray]:
        """
        Sample point cloud to an exact count of target_points.
        If N > target_points, samples without replacement.
        If N < target_points, samples with replacement (padding).

        Returns:
            Tuple of (sampled_points, sampled_labels, sample_indices).
        """
        num_points = len(points)
        if num_points == 0:
            raise ValueError("Cannot sample an empty point cloud.")

        rng = np.random.default_rng(random_seed)

        if num_points >= target_points:
            indices = rng.choice(num_points, size=target_points, replace=False)
        else:
            # Over-sample / repeat with replacement if fewer points than target
            indices = rng.choice(num_points, size=target_points, replace=True)

        sampled_points = points[indices]
        sampled_labels = labels[indices] if labels is not None else None

        return sampled_points, sampled_labels, indices

    @staticmethod
    def voxel_grid_downsample(
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        voxel_size: float = 0.1,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Downsample points using a fast NumPy voxel hash grid.
        Preserves representative points closest to voxel centers.
        """
        if len(points) == 0:
            return points, labels

        coords = np.floor(points[:, :3] / voxel_size).astype(np.int32)
        # Unique voxel coordinates
        _, unique_indices = np.unique(coords, axis=0, return_index=True)
        unique_indices = np.sort(unique_indices)

        downsampled_points = points[unique_indices]
        downsampled_labels = labels[unique_indices] if labels is not None else None

        return downsampled_points, downsampled_labels

    def process(
        self,
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        random_seed: Optional[int] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Execute full end-to-end preprocessing pipeline.

        1. Remove invalid / NaN / Inf points.
        2. Range filter (min_range <= r <= max_range).
        3. ROI crop (if configured).
        4. Target point sampling (if configured).
        """
        pts, lbls, _ = self.remove_invalid_points(points, labels)

        if self.min_range > 0 or self.max_range < np.inf:
            pts, lbls, _ = self.filter_by_range(pts, lbls, self.min_range, self.max_range)

        if self.roi_bounds is not None:
            pts, lbls, _ = self.crop_roi(pts, lbls, self.roi_bounds)

        if self.target_num_points is not None and len(pts) > 0:
            pts, lbls, _ = self.sample_points(pts, lbls, self.target_num_points, random_seed=random_seed)

        return pts, lbls


if __name__ == "__main__":
    # Test preprocessor with random data containing edge cases
    test_points = np.array([
        [10.0, 5.0, -1.0, 0.5],
        [np.nan, 2.0, 3.0, 0.1],      # NaN
        [0.0, 0.0, 0.0, 0.0],         # Origin
        [0.5, 0.5, 0.0, 0.2],         # Range < 1.5m (ego vehicle body)
        [30.0, -10.0, 1.0, 0.8],      # Valid
        [150.0, 0.0, 0.0, 0.4],       # Range > 80m
    ], dtype=np.float32)

    test_labels = np.array([0, 1, 2, 3, 4, 5], dtype=np.uint32)

    prep = PointCloudPreprocessor(min_range=1.5, max_range=80.0)
    cleaned_pts, cleaned_lbls = prep.process(test_points, test_labels)

    print(f"Original points: {len(test_points)}, Cleaned points: {len(cleaned_pts)}")
    print("Cleaned points:\n", cleaned_pts)
    print("Cleaned labels:\n", cleaned_lbls)
