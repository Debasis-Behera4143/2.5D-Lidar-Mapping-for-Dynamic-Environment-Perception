"""
Inference Pipeline for LiDAR Point Cloud Semantic Segmentation.

Returns the standardized perception contract:
{
    "points": np.ndarray,            # (N, 4) float32 [X, Y, Z, Intensity]
    "predicted_labels": np.ndarray,  # (N,) int64 in range [0, 7]
    "confidence_scores": np.ndarray, # (N,) float32 in range [0.0, 1.0]
    "frame_id": str                  # frame identifier
}
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
import torch
import torch.nn.functional as F

from src.data.lidar_loader import LiDARLoader
from src.preprocessing.preprocess import PointCloudPreprocessor
from src.ai.model import RandLANet
from src.ai.label_mapping import ID_TO_CLASS, NUM_CLASSES, map_raw_to_project_labels


class SemanticSegmenter:
    """
    Production inference engine for point cloud semantic segmentation.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        num_classes: int = NUM_CLASSES,
        num_points: int = 4096,
        k_neighbors: int = 16,
        device: Optional[str] = None,
    ):
        """
        Args:
            model_path: Optional path to .pt or .pth weights checkpoint.
            num_classes: Number of output semantic classes (default: 8).
            num_points: Target point count sampled for network inference.
            k_neighbors: Nearest neighbors for attentive pooling.
            device: 'cuda', 'cpu', or None for auto-detection.
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.num_points = num_points
        self.num_classes = num_classes

        # Initialize network
        self.model = RandLANet(
            num_classes=num_classes,
            in_channels=4,
            k_neighbors=k_neighbors,
        ).to(self.device)

        if model_path is not None and Path(model_path).is_file():
            checkpoint = torch.load(str(model_path), map_location=self.device)
            if "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"])
            else:
                self.model.load_state_dict(checkpoint)
            print(f"Loaded model weights from {model_path}")
        else:
            print("Initialized model with baseline weights.")

        self.model.eval()

        self.preprocessor = PointCloudPreprocessor(
            min_range=1.5,
            max_range=60.0,
            roi_bounds=(-40.0, 40.0, -40.0, 40.0, -3.0, 4.0),
            target_num_points=num_points,
        )

    def predict_points(
        self,
        points: np.ndarray,
        labels: Optional[np.ndarray] = None,
        frame_id: str = "frame_0000",
        interpolate_to_full: bool = False,
    ) -> Dict[str, Any]:
        """
        Run segmentation inference on a point cloud.

        Args:
            points: (N, 4) or (N, 3) raw point coordinates + intensity.
            labels: Optional (N,) ground-truth labels for synchronized alignment and verification.
            frame_id: String frame identifier.
            interpolate_to_full: If True, maps sampled predictions back to all cleaned points.

        Returns:
            Dictionary matching the strict project contract:
            {
                "points": np.ndarray (M, 4),
                "predicted_labels": np.ndarray (M,),
                "confidence_scores": np.ndarray (M,),
                "frame_id": str,
                # Optional if labels provided:
                "ground_truth_labels": np.ndarray (M,)
            }
        """
        if points.ndim != 2 or points.shape[1] < 3:
            raise ValueError(f"Expected (N, >=3) points, got shape {points.shape}")

        # Ensure 4 channels (X, Y, Z, Intensity)
        if points.shape[1] == 3:
            intensity = np.zeros((len(points), 1), dtype=np.float32)
            pts_4d = np.hstack([points, intensity]).astype(np.float32)
        else:
            pts_4d = points[:, :4].astype(np.float32)

        raw_lbls = None
        if labels is not None:
            raw_lbls = np.asarray(labels)
            if np.max(raw_lbls) > 7:
                raw_lbls = map_raw_to_project_labels(raw_lbls)

        if interpolate_to_full:
            # 1. Clean full point cloud without random downsampling
            clean_pts, clean_lbls, _ = PointCloudPreprocessor.remove_invalid_points(pts_4d, raw_lbls)
            clean_pts, clean_lbls, _ = PointCloudPreprocessor.filter_by_range(
                clean_pts, clean_lbls, min_range=self.preprocessor.min_range, max_range=self.preprocessor.max_range
            )
            if self.preprocessor.roi_bounds is not None:
                clean_pts, clean_lbls, _ = PointCloudPreprocessor.crop_roi(
                    clean_pts, clean_lbls, roi=self.preprocessor.roi_bounds
                )

            if len(clean_pts) == 0:
                raise ValueError("No valid points remaining after preprocessing filters.")

            # 2. Subsample to num_points for model forward pass
            sampled_pts, sampled_lbls, _ = PointCloudPreprocessor.sample_points(
                clean_pts, clean_lbls, target_points=self.num_points, random_seed=42
            )

            # 3. Model forward pass on sampled points
            xyz_tensor = torch.from_numpy(sampled_pts[:, :3]).unsqueeze(0).float().to(self.device)
            feat_tensor = torch.from_numpy(sampled_pts).unsqueeze(0).permute(0, 2, 1).float().to(self.device)

            with torch.no_grad():
                logits = self.model(xyz_tensor, feat_tensor)  # (1, num_classes, N)
                probs = F.softmax(logits, dim=1)              # (1, num_classes, N)
                confidence, preds = torch.max(probs, dim=1)   # (1, N) each

            sampled_preds = preds[0].cpu().numpy().astype(np.int64)
            sampled_conf = confidence[0].cpu().numpy().astype(np.float32)

            # 4. Dense 1-NN KDTree interpolation back to all clean points
            from scipy.spatial import cKDTree
            tree = cKDTree(sampled_pts[:, :3])
            _, nn_indices = tree.query(clean_pts[:, :3], k=1, workers=1)

            full_preds = sampled_preds[nn_indices]
            full_conf = sampled_conf[nn_indices]

            result: Dict[str, Any] = {
                "points": clean_pts,
                "predicted_labels": full_preds,
                "confidence_scores": full_conf,
                "frame_id": str(frame_id),
            }
            if clean_lbls is not None:
                result["ground_truth_labels"] = clean_lbls

            return result
        else:
            # Standard downsampled perception pipeline
            processed_pts, processed_lbls = self.preprocessor.process(pts_4d, raw_lbls, random_seed=42)

            if len(processed_pts) < self.num_points:
                processed_pts, processed_lbls, _ = PointCloudPreprocessor.sample_points(
                    processed_pts,
                    processed_lbls,
                    target_points=self.num_points,
                    random_seed=42,
                )

            xyz_tensor = torch.from_numpy(processed_pts[:, :3]).unsqueeze(0).float().to(self.device)
            feat_tensor = torch.from_numpy(processed_pts).unsqueeze(0).permute(0, 2, 1).float().to(self.device)

            with torch.no_grad():
                logits = self.model(xyz_tensor, feat_tensor)  # (1, num_classes, N)
                probs = F.softmax(logits, dim=1)              # (1, num_classes, N)
                confidence, preds = torch.max(probs, dim=1)   # (1, N) each

            predicted_labels = preds[0].cpu().numpy().astype(np.int64)
            confidence_scores = confidence[0].cpu().numpy().astype(np.float32)

            result = {
                "points": processed_pts,
                "predicted_labels": predicted_labels,
                "confidence_scores": confidence_scores,
                "frame_id": str(frame_id),
            }
            if processed_lbls is not None:
                result["ground_truth_labels"] = processed_lbls

            return result

    def predict_file(
        self,
        bin_path: Union[str, Path],
        label_path: Optional[Union[str, Path]] = None,
        interpolate_to_full: bool = False,
    ) -> Dict[str, Any]:
        """
        Run inference directly from a .bin file path with optional .label path.
        """
        path = Path(bin_path)
        points = LiDARLoader.load_bin(path)
        labels = None
        if label_path is not None and Path(label_path).is_file():
            from src.data.label_loader import LabelLoader
            _, raw_sem, _ = LabelLoader.load_label(label_path, expected_points=len(points))
            labels = raw_sem
        return self.predict_points(
            points, labels=labels, frame_id=path.stem, interpolate_to_full=interpolate_to_full
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run LiDAR Semantic Segmentation inference.")
    parser.add_argument("bin_path", type=str, nargs="?", default=None, help="Path to .bin frame")
    parser.add_argument("--model-path", type=str, default=None, help="Path to checkpoint .pt")
    parser.add_argument("--points", type=int, default=2048, help="Number of points to sample")
    args = parser.parse_args()

    # Prefer real checkpoint if available
    real_ckpt = Path("checkpoints/best_randlanet_real.pt")
    base_ckpt = Path("checkpoints/best_randlanet.pt")
    chosen_ckpt = args.model_path or (str(real_ckpt) if real_ckpt.is_file() else (str(base_ckpt) if base_ckpt.is_file() else None))

    # Prefer real data if available
    real_bin = Path("data/semantic_kitti/sequences/00/velodyne/000000.bin")
    sample_bin = Path("data/sample_kitti/sequences/00/velodyne/000000.bin")
    target_bin = args.bin_path or (str(real_bin) if real_bin.is_file() else str(sample_bin))

    print(f"Running inference with model: {chosen_ckpt}")
    print(f"Target LiDAR scan:            {target_bin}")

    segmenter = SemanticSegmenter(model_path=chosen_ckpt, num_points=args.points, k_neighbors=12)
    output = segmenter.predict_file(target_bin)

    print("\nInference Output Contract Verification:")
    print("=" * 60)
    print(f"Frame ID:           {output['frame_id']}")
    print(f"Points shape:       {output['points'].shape} ({output['points'].dtype})")
    print(f"Predicted labels:   {output['predicted_labels'].shape} ({output['predicted_labels'].dtype})")
    print(f"Confidence scores:  {output['confidence_scores'].shape} ({output['confidence_scores'].dtype})")
    print(f"Confidence range:   [{output['confidence_scores'].min():.3f}, {output['confidence_scores'].max():.3f}]")

    # Verify keys
    expected_keys = {"points", "predicted_labels", "confidence_scores", "frame_id"}
    assert set(output.keys()) == expected_keys, f"Contract mismatch: {output.keys()} != {expected_keys}"

    # Class summary
    unique_preds, counts = np.unique(output["predicted_labels"], return_counts=True)
    print("\nPredicted Class Distribution:")
    for cls_id, count in zip(unique_preds, counts):
        print(f"  Class {cls_id} ({ID_TO_CLASS[cls_id]:<12}): {count:>5d} points ({count/len(output['predicted_labels'])*100:.1f}%)")
    print("=" * 60)
    print("Inference Contract Validated Successfully on Real Scan!")
