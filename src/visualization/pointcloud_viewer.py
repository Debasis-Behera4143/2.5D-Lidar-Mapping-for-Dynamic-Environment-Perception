"""
LiDAR Point Cloud Visualizer.

Provides 3D point cloud visualization using Open3D:
- Intensity-based false-color rendering
- Height (Z) gradient rendering
- Semantic label rendering using the 8-class project taxonomy
- Side-by-side Ground Truth vs Prediction comparison
- Graceful headless fallback (exports PLY/PCD or generates 2.5D BEV projection)
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np

from src.ai.label_mapping import colorize_mapped_labels, map_raw_to_project_labels, ID_TO_CLASS, PROJECT_CLASSES

# Check for Open3D availability
try:
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


class PointCloudVisualizer:
    """
    Open3D-based interactive visualizer with headless and export fallbacks.
    """

    @staticmethod
    def _compute_height_colors(z_coords: np.ndarray) -> np.ndarray:
        """Compute height gradient from blue (low) -> green -> red (high)."""
        z_min, z_max = np.min(z_coords), np.max(z_coords)
        if z_max == z_min:
            norm_z = np.zeros_like(z_coords)
        else:
            norm_z = np.clip((z_coords - z_min) / (z_max - z_min), 0.0, 1.0)

        # Colormap approximation: Blue -> Cyan -> Green -> Yellow -> Red
        colors = np.zeros((len(z_coords), 3), dtype=np.float32)
        colors[:, 0] = np.clip(2.0 * norm_z - 0.5, 0.0, 1.0)                 # Red
        colors[:, 1] = np.clip(1.0 - np.abs(2.0 * norm_z - 1.0), 0.0, 1.0)  # Green
        colors[:, 2] = np.clip(1.0 - 2.0 * norm_z, 0.0, 1.0)                # Blue
        return colors

    @staticmethod
    def _compute_intensity_colors(intensity: np.ndarray) -> np.ndarray:
        """Compute intensity colormap (Viridis / Jet style gradient)."""
        i_min, i_max = np.min(intensity), np.max(intensity)
        if i_max == i_min:
            norm_i = np.zeros_like(intensity)
        else:
            norm_i = np.clip((intensity - i_min) / (i_max - i_min), 0.0, 1.0)

        colors = np.zeros((len(intensity), 3), dtype=np.float32)
        # Smooth copper/fire gradient: Black -> Orange -> Yellow -> White
        colors[:, 0] = np.clip(1.5 * norm_i, 0.0, 1.0)
        colors[:, 1] = np.clip(1.5 * norm_i - 0.3, 0.0, 1.0)
        colors[:, 2] = np.clip(2.0 * norm_i - 1.0, 0.0, 1.0)
        return colors

    @classmethod
    def visualize(
        cls,
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        color_mode: str = "auto",
        window_name: str = "LiDAR Point Cloud Viewer",
        save_path: Optional[Union[str, Path]] = None,
        headless: bool = False,
    ) -> bool:
        """
        Visualize a point cloud.

        Args:
            points: (N, 3) or (N, 4) array.
            labels: Optional (N,) semantic labels (either raw or mapped 0-7).
            color_mode: 'auto', 'semantic', 'intensity', 'height', or 'white'.
            window_name: Window title bar.
            save_path: Optional path to save exported PLY/image.
            headless: If True, skips opening GUI window.

        Returns:
            bool: True if visualized/saved successfully.
        """
        xyz = points[:, :3].astype(np.float64)

        # Determine colors
        if color_mode == "semantic" and labels is not None:
            # Check if raw or already mapped
            if np.max(labels) > 7:
                mapped = map_raw_to_project_labels(labels)
            else:
                mapped = labels
            colors = colorize_mapped_labels(mapped, as_float=True)
        elif color_mode == "intensity" and points.shape[1] >= 4:
            colors = cls._compute_intensity_colors(points[:, 3])
        elif color_mode == "height":
            colors = cls._compute_height_colors(xyz[:, 2])
        elif color_mode == "auto":
            if labels is not None:
                mapped = map_raw_to_project_labels(labels) if np.max(labels) > 7 else labels
                colors = colorize_mapped_labels(mapped, as_float=True)
            elif points.shape[1] >= 4:
                colors = cls._compute_intensity_colors(points[:, 3])
            else:
                colors = cls._compute_height_colors(xyz[:, 2])
        else:
            colors = np.ones((len(xyz), 3), dtype=np.float32) * 0.8

        if HAS_OPEN3D:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(xyz)
            pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float64))

            if save_path:
                save_p = Path(save_path)
                if save_p.suffix.lower() in [".ply", ".pcd"]:
                    save_p.parent.mkdir(parents=True, exist_ok=True)
                    o3d.io.write_point_cloud(str(save_p), pcd)
                    print(f"Point cloud saved to {save_p.resolve()}")

            if not headless:
                print(f"Opening Open3D viewer: '{window_name}' (Press 'Q' or close window to exit)...")
                o3d.visualization.draw_geometries(
                    [pcd],
                    window_name=window_name,
                    width=1280,
                    height=720,
                )
            return True
        else:
            # Fallback when Open3D is not installed in current Python env
            print(f"[Viewer Info] Open3D is not installed in the active Python environment.")
            if save_path:
                cls.export_ply_raw(xyz, colors, Path(save_path))
                print(f"[Viewer Info] Exported raw PLY point cloud to: {Path(save_path).resolve()}")
            cls.render_bev_ascii(xyz)
            return False

    @staticmethod
    def export_ply_raw(
        points: np.ndarray,
        colors: Optional[np.ndarray],
        out_path: Union[str, Path],
    ) -> None:
        """
        Write standard ASCII PLY file directly without any external library.
        Can be opened in MeshLab, CloudCompare, Blender, or any 3D tool.
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        num_points = len(points)

        header = [
            "ply",
            "format ascii 1.0",
            f"element vertex {num_points}",
            "property float x",
            "property float y",
            "property float z",
        ]
        if colors is not None:
            header.extend([
                "property uchar red",
                "property uchar green",
                "property uchar blue",
            ])
        header.append("end_header\n")

        with open(out_path, "w") as f:
            f.write("\n".join(header))
            if colors is not None:
                # Convert colors to uint8
                c_u8 = (colors * 255).astype(np.uint8) if colors.dtype == np.float32 or colors.dtype == np.float64 else colors.astype(np.uint8)
                for i in range(num_points):
                    p = points[i]
                    c = c_u8[i]
                    f.write(f"{p[0]:.3f} {p[1]:.3f} {p[2]:.3f} {c[0]} {c[1]} {c[2]}\n")
            else:
                for i in range(num_points):
                    p = points[i]
                    f.write(f"{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}\n")

    @staticmethod
    def render_bev_ascii(points: np.ndarray, grid_size: int = 30) -> None:
        """
        Print Bird's Eye View (BEV, top-down X vs Y) ASCII density map for CLI inspection.
        """
        x = points[:, 0]
        y = points[:, 1]
        x_min, x_max = np.min(x), np.max(x)
        y_min, y_max = np.min(y), np.max(y)

        hist, _, _ = np.histogram2d(x, y, bins=(grid_size, grid_size), range=[[x_min, x_max], [y_min, y_max]])
        chars = " .:-=+*#%@"
        max_val = np.max(hist) if np.max(hist) > 0 else 1.0

        print(f"\n--- Bird's Eye View (BEV) Density [X: {x_min:.1f} to {x_max:.1f}m, Y: {y_min:.1f} to {y_max:.1f}m] ---")
        for row in reversed(hist.T):
            line = "".join(chars[min(int((val / max_val) * (len(chars) - 1)), len(chars) - 1)] for val in row)
            print(line)
        print("----------------------------------------------------------------------------\n")


    @classmethod
    def compare_ground_truth_vs_prediction(
        cls,
        points: np.ndarray,
        gt_labels: np.ndarray,
        pred_labels: np.ndarray,
        save_dir: Union[str, Path] = "data/outputs/visualizations",
        frame_id: str = "000000",
        headless: bool = True,
    ) -> Dict[str, Any]:
        """
        Visual comparison between Ground Truth and Predictions:
        1. Ground Truth Semantic point cloud
        2. Predicted Semantic point cloud
        3. Error map: Green = Correct, Red = Misclassified

        Exports PLY point clouds for external 3D visualization.
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        xyz = points[:, :3].astype(np.float32)

        # Map labels if in raw format
        gt_mapped = map_raw_to_project_labels(gt_labels) if np.max(gt_labels) > 7 else gt_labels
        pred_mapped = map_raw_to_project_labels(pred_labels) if np.max(pred_labels) > 7 else pred_labels

        # 1. Colors
        gt_colors = colorize_mapped_labels(gt_mapped, as_float=True)
        pred_colors = colorize_mapped_labels(pred_mapped, as_float=True)

        # 2. Error Map: Green = Correct, Red = Incorrect
        is_correct = (gt_mapped == pred_mapped)
        error_colors = np.zeros((len(points), 3), dtype=np.float32)
        error_colors[is_correct] = [0.2, 0.8, 0.2]   # Green
        error_colors[~is_correct] = [0.9, 0.1, 0.1]  # Red

        # 3. Export PLY files
        gt_ply = save_path / f"{frame_id}_gt_semantic.ply"
        pred_ply = save_path / f"{frame_id}_pred_semantic.ply"
        err_ply = save_path / f"{frame_id}_error_map.ply"

        cls.export_ply_raw(xyz, gt_colors, gt_ply)
        cls.export_ply_raw(xyz, pred_colors, pred_ply)
        cls.export_ply_raw(xyz, error_colors, err_ply)

        correct_count = int(np.sum(is_correct))
        total_count = len(points)
        accuracy = 100.0 * correct_count / max(1, total_count)

        print("\n" + "=" * 70)
        print(f"VISUAL VERIFICATION & ERROR ANALYSIS: Frame {frame_id}")
        print("=" * 70)
        print(f"Total Points:             {total_count:,d}")
        print(f"Correctly Classified:     {correct_count:,d} ({accuracy:.2f}%) [GREEN]")
        print(f"Misclassified (Errors):   {total_count - correct_count:,d} ({100.0 - accuracy:.2f}%) [RED]")
        print(f"Exported Ground Truth PLY: {gt_ply.resolve()}")
        print(f"Exported Prediction PLY:   {pred_ply.resolve()}")
        print(f"Exported Error Map PLY:    {err_ply.resolve()}")
        print("=" * 70)

        # Print BEV density maps
        print("\nTop-Down Bird's Eye View (BEV) of Ground-Truth Points:")
        cls.render_bev_ascii(xyz)

        return {
            "total_points": total_count,
            "correct_points": correct_count,
            "misclassified_points": total_count - correct_count,
            "accuracy": accuracy,
            "gt_ply": str(gt_ply),
            "pred_ply": str(pred_ply),
            "error_ply": str(err_ply),
        }


if __name__ == "__main__":
    import argparse
    from src.data.lidar_loader import LiDARLoader
    from src.data.label_loader import LabelLoader
    from src.ai.inference import SemanticSegmenter

    parser = argparse.ArgumentParser(description="LiDAR Visualizer & Comparison Engine")
    parser.add_argument("--bin", type=str, default=None, help="Path to .bin file")
    parser.add_argument("--label", type=str, default=None, help="Path to .label file")
    parser.add_argument("--checkpoint", type=str, default=None, help="Model checkpoint")
    args = parser.parse_args()

    bin_file = args.bin or "data/semantic_kitti/sequences/00/velodyne/000000.bin"
    lbl_file = args.label or "data/semantic_kitti/sequences/00/labels/000000.label"

    if Path(bin_file).is_file() and Path(lbl_file).is_file():
        # Load real frame
        pts = LiDARLoader.load_bin(bin_file)
        _, raw_sem, _ = LabelLoader.load_label(lbl_file, expected_points=len(pts))

        # Run inference with synchronized label processing for 100% spatial-semantic alignment
        segmenter = SemanticSegmenter(
            model_path=args.checkpoint or "checkpoints/best_randlanet_real.pt",
            num_points=2048,
            k_neighbors=12,
        )
        pred_dict = segmenter.predict_points(pts, labels=raw_sem, frame_id=Path(bin_file).stem)

        sampled_pts = pred_dict["points"]
        preds = pred_dict["predicted_labels"]
        # Exact ground truth aligned with sampled point coordinates
        gt_mapped = pred_dict["ground_truth_labels"]

        PointCloudVisualizer.compare_ground_truth_vs_prediction(
            points=sampled_pts,
            gt_labels=gt_mapped,
            pred_labels=preds,
            save_dir="data/outputs/visualizations",
            frame_id=Path(bin_file).stem,
            headless=True,
        )
    else:
        # Fallback to test with synthetic points
        from src.data.sample_generator import generate_synthetic_kitti_frame
        pts, lbls = generate_synthetic_kitti_frame(num_points=1000)
        PointCloudVisualizer.visualize(
            pts, lbls, color_mode="semantic", headless=True, save_path="data/outputs/visualizations/sample_pointcloud.ply"
        )

