"""
Synthetic SemanticKITTI sample frame generator.

Generates realistic Velodyne HDL-64E binary point clouds (.bin) and SemanticKITTI
label files (.label) for offline unit testing, integration tests, and immediate
pipeline validation without requiring the full 80GB dataset download.
"""

from pathlib import Path
from typing import Tuple
import numpy as np


def generate_synthetic_kitti_frame(
    num_points: int = 15000,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesize a realistic urban driving LiDAR frame.

    Synthesizes:
    - Road surface (z ≈ -1.73m, class 40)
    - Sidewalk borders (class 48)
    - Buildings (class 50)
    - Vegetation / Trees (class 70)
    - Vehicles (class 10, with instance IDs)
    - Pedestrians (class 30, with instance IDs)
    - Poles / Traffic Signs (class 80)
    - Outliers / Unlabeled (class 0)

    Args:
        num_points: Target number of LiDAR points.
        seed: Random seed for reproducibility.

    Returns:
        points: (N, 4) float32 array of [X, Y, Z, Intensity].
        raw_labels: (N,) uint32 array of (instance_id << 16) | semantic_id.
    """
    rng = np.random.default_rng(seed)

    points_list = []
    labels_list = []

    # 1. Road surface (class 40, ~40% of points)
    n_road = int(num_points * 0.40)
    x_road = rng.uniform(-25.0, 50.0, n_road)
    y_road = rng.uniform(-4.0, 4.0, n_road)
    z_road = rng.normal(-1.73, 0.05, n_road)
    i_road = rng.uniform(0.15, 0.45, n_road)
    pts_road = np.column_stack([x_road, y_road, z_road, i_road])
    lbl_road = np.full(n_road, 40, dtype=np.uint32)
    points_list.append(pts_road)
    labels_list.append(lbl_road)

    # 2. Sidewalks (class 48, ~15% of points)
    n_sw = int(num_points * 0.15)
    half_sw = n_sw // 2
    # Left sidewalk: y in [4.0, 7.0]
    x_sw_l = rng.uniform(-20.0, 45.0, half_sw)
    y_sw_l = rng.uniform(4.0, 7.0, half_sw)
    z_sw_l = rng.normal(-1.58, 0.04, half_sw)
    i_sw_l = rng.uniform(0.20, 0.50, half_sw)
    # Right sidewalk: y in [-7.0, -4.0]
    x_sw_r = rng.uniform(-20.0, 45.0, n_sw - half_sw)
    y_sw_r = rng.uniform(-7.0, -4.0, n_sw - half_sw)
    z_sw_r = rng.normal(-1.58, 0.04, n_sw - half_sw)
    i_sw_r = rng.uniform(0.20, 0.50, n_sw - half_sw)
    pts_sw = np.vstack([
        np.column_stack([x_sw_l, y_sw_l, z_sw_l, i_sw_l]),
        np.column_stack([x_sw_r, y_sw_r, z_sw_r, i_sw_r]),
    ])
    lbl_sw = np.full(n_sw, 48, dtype=np.uint32)
    points_list.append(pts_sw)
    labels_list.append(lbl_sw)

    # 3. Buildings (class 50, ~15% of points)
    n_bld = int(num_points * 0.15)
    half_bld = n_bld // 2
    # Left building facade: y in [7.0, 15.0], z in [-1.5, 6.0]
    x_bld_l = rng.uniform(-15.0, 40.0, half_bld)
    y_bld_l = rng.uniform(7.5, 12.0, half_bld)
    z_bld_l = rng.uniform(-1.5, 5.5, half_bld)
    i_bld_l = rng.uniform(0.3, 0.8, half_bld)
    # Right building facade: y in [-12.0, -7.5]
    x_bld_r = rng.uniform(-15.0, 40.0, n_bld - half_bld)
    y_bld_r = rng.uniform(-12.0, -7.5, n_bld - half_bld)
    z_bld_r = rng.uniform(-1.5, 5.5, n_bld - half_bld)
    i_bld_r = rng.uniform(0.3, 0.8, n_bld - half_bld)
    pts_bld = np.vstack([
        np.column_stack([x_bld_l, y_bld_l, z_bld_l, i_bld_l]),
        np.column_stack([x_bld_r, y_bld_r, z_bld_r, i_bld_r]),
    ])
    lbl_bld = np.full(n_bld, 50, dtype=np.uint32)
    points_list.append(pts_bld)
    labels_list.append(lbl_bld)

    # 4. Vegetation (class 70, ~12% of points)
    n_veg = int(num_points * 0.12)
    x_veg = rng.uniform(-10.0, 35.0, n_veg)
    side = rng.choice([-1.0, 1.0], size=n_veg)
    y_veg = side * rng.uniform(5.5, 9.0, n_veg)
    z_veg = rng.uniform(-0.5, 4.0, n_veg)
    i_veg = rng.uniform(0.1, 0.6, n_veg)
    pts_veg = np.column_stack([x_veg, y_veg, z_veg, i_veg])
    lbl_veg = np.full(n_veg, 70, dtype=np.uint32)
    points_list.append(pts_veg)
    labels_list.append(lbl_veg)

    # 5. Vehicles (class 10, ~10% of points, 2 distinct instances)
    n_veh = int(num_points * 0.10)
    n_car1 = n_veh // 2
    n_car2 = n_veh - n_car1

    # Car 1: Ahead in right lane (instance_id = 1)
    x_c1 = rng.uniform(8.0, 12.5, n_car1)
    y_c1 = rng.uniform(-2.5, -0.8, n_car1)
    z_c1 = rng.uniform(-1.6, -0.2, n_car1)
    i_c1 = rng.uniform(0.6, 0.95, n_car1)
    pts_c1 = np.column_stack([x_c1, y_c1, z_c1, i_c1])
    lbl_c1 = np.full(n_car1, (1 << 16) | 10, dtype=np.uint32)

    # Car 2: Parked on left side (instance_id = 2)
    x_c2 = rng.uniform(18.0, 22.0, n_car2)
    y_c2 = rng.uniform(1.2, 2.9, n_car2)
    z_c2 = rng.uniform(-1.6, -0.2, n_car2)
    i_c2 = rng.uniform(0.5, 0.90, n_car2)
    pts_c2 = np.column_stack([x_c2, y_c2, z_c2, i_c2])
    lbl_c2 = np.full(n_car2, (2 << 16) | 10, dtype=np.uint32)

    points_list.extend([pts_c1, pts_c2])
    labels_list.extend([lbl_c1, lbl_c2])

    # 6. Pedestrians (class 30, ~4% of points, instance_id = 3)
    n_ped = int(num_points * 0.04)
    x_ped = rng.uniform(6.0, 7.0, n_ped)
    y_ped = rng.uniform(4.5, 5.2, n_ped)
    z_ped = rng.uniform(-1.5, 0.3, n_ped)
    i_ped = rng.uniform(0.2, 0.6, n_ped)
    pts_ped = np.column_stack([x_ped, y_ped, z_ped, i_ped])
    lbl_ped = np.full(n_ped, (3 << 16) | 30, dtype=np.uint32)
    points_list.append(pts_ped)
    labels_list.append(lbl_ped)

    # 7. Poles / Signs (class 80, ~3% of points)
    n_pole = int(num_points * 0.03)
    x_pole = rng.normal(12.0, 0.15, n_pole)
    y_pole = rng.normal(4.2, 0.15, n_pole)
    z_pole = rng.uniform(-1.6, 2.5, n_pole)
    i_pole = rng.uniform(0.7, 0.98, n_pole)
    pts_pole = np.column_stack([x_pole, y_pole, z_pole, i_pole])
    lbl_pole = np.full(n_pole, 80, dtype=np.uint32)
    points_list.append(pts_pole)
    labels_list.append(lbl_pole)

    # 8. Outliers / Unlabeled (class 0, remainder)
    current_count = sum(len(p) for p in points_list)
    n_rem = max(0, num_points - current_count)
    if n_rem > 0:
        x_rem = rng.uniform(-30.0, 60.0, n_rem)
        y_rem = rng.uniform(-20.0, 20.0, n_rem)
        z_rem = rng.uniform(-3.0, 8.0, n_rem)
        i_rem = rng.uniform(0.0, 0.3, n_rem)
        pts_rem = np.column_stack([x_rem, y_rem, z_rem, i_rem])
        lbl_rem = np.full(n_rem, 0, dtype=np.uint32)
        points_list.append(pts_rem)
        labels_list.append(lbl_rem)

    points = np.vstack(points_list).astype(np.float32)
    raw_labels = np.concatenate(labels_list).astype(np.uint32)

    # Shuffle to simulate unorganized LiDAR scanner return
    perm = rng.permutation(len(points))
    return points[perm], raw_labels[perm]


def save_kitti_frame(
    points: np.ndarray,
    raw_labels: np.ndarray,
    bin_path: Path,
    label_path: Path,
) -> None:
    """
    Save LiDAR points to .bin and labels to .label following SemanticKITTI specs.
    """
    bin_path = Path(bin_path)
    label_path = Path(label_path)

    bin_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.parent.mkdir(parents=True, exist_ok=True)

    # .bin: float32 binary array of shape (N, 4)
    points.astype(np.float32).tofile(str(bin_path))
    # .label: uint32 binary array of shape (N,)
    raw_labels.astype(np.uint32).tofile(str(label_path))


def create_sample_dataset(
    output_dir: Path,
    sequence_id: str = "00",
    num_frames: int = 3,
    points_per_frame: int = 20000,
) -> Path:
    """
    Create a complete sample SemanticKITTI dataset structure with multiple frames.
    """
    output_dir = Path(output_dir)
    seq_dir = output_dir / "sequences" / sequence_id
    velo_dir = seq_dir / "velodyne"
    labels_dir = seq_dir / "labels"

    velo_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    for frame_idx in range(num_frames):
        frame_name = f"{frame_idx:06d}"
        bin_path = velo_dir / f"{frame_name}.bin"
        label_path = labels_dir / f"{frame_name}.label"

        pts, lbls = generate_synthetic_kitti_frame(
            num_points=points_per_frame,
            seed=42 + frame_idx,
        )
        save_kitti_frame(pts, lbls, bin_path, label_path)

    return output_dir


if __name__ == "__main__":
    sample_dir = Path("data/sample_kitti")
    created_path = create_sample_dataset(sample_dir, num_frames=3, points_per_frame=25000)
    print(f"Created sample SemanticKITTI dataset at: {created_path.resolve()}")
