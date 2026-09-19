"""
LiDAR Semantic Segmentation inference service.

Provides a lazy-loaded singleton wrapper around Member 1's SemanticSegmenter,
guaranteeing single-model memory footprint, evaluation mode with torch.inference_mode(),
device auto-detection, and JSON-safe perception contracts.

NOTE: Current checkpoints are baseline prototype models; performance claims
should be backed by empirical test evaluation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch

from src.ai.inference import SemanticSegmenter
from src.ai.label_mapping import ID_TO_CLASS, NUM_CLASSES
from src.backend.config import PROJECT_ROOT, get_checkpoint_path, get_compute_device
from src.backend.services.serialization import to_json_safe
from src.backend.utils.errors import (
    CheckpointNotFoundError,
    InferenceError,
    InvalidInputError,
    SampleNotFoundError,
)


class InferenceService:
    """
    Singleton inference service for point-cloud semantic segmentation.
    """

    _instance: Optional["InferenceService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InferenceService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, checkpoint_path: Optional[Path] = None, device: Optional[torch.device] = None):
        if getattr(self, "_initialized", False):
            return

        self.checkpoint_path = checkpoint_path or get_checkpoint_path()
        self.device = device or get_compute_device()
        self.segmenter: Optional[SemanticSegmenter] = None
        self._model_loaded: bool = False
        self._initialized = True

    def is_loaded(self) -> bool:
        """True if model weights are loaded into memory."""
        return self._model_loaded

    def load_model(self) -> None:
        """
        Lazily initialize and load model weights once into the active device.
        """
        if self._model_loaded and self.segmenter is not None:
            return

        ckpt = self.checkpoint_path
        if not ckpt.is_file():
            raise CheckpointNotFoundError(
                f"Required model checkpoint does not exist: {ckpt}. "
                "Ensure checkpoints/best_randlanet_real.pt or fallback is present."
            )

        try:
            # Reuses Member 1 SemanticSegmenter
            self.segmenter = SemanticSegmenter(
                model_path=str(ckpt),
                num_classes=NUM_CLASSES,
                num_points=4096,
                device=str(self.device),
            )
            # Ensure model is strictly in eval mode
            self.segmenter.model.eval()
            self._model_loaded = True
        except Exception as e:
            raise InferenceError(f"Failed to initialize SemanticSegmenter: {e}")

    def run_inference(
        self,
        bin_path: Union[str, Path],
        label_path: Optional[Union[str, Path]] = None,
        num_points: int = 4096,
        interpolate_to_full: bool = False,
        preview_points_limit: int = 2000,
    ) -> Dict[str, Any]:
        """
        Execute semantic segmentation on a LiDAR point cloud file.

        Args:
            bin_path: Filesystem path to binary Velodyne HDL-64E scan (.bin).
            label_path: Optional path to synchronized SemanticKITTI label file (.label).
            num_points: Point count sampled for network forward pass.
            interpolate_to_full: If True, interpolates labels back to dense cloud via 1-NN.
            preview_points_limit: Maximum number of points returned for visualization.

        Returns:
            JSON-safe dictionary containing:
            points, predicted_labels, confidence_scores, frame_id, device,
            point_count, spatial_bounds, class_distribution, confidence_information,
            preview_points, and optional evaluation_information.
        """
        # Validate input path
        path = Path(bin_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path

        if not path.is_file():
            raise SampleNotFoundError(f"LiDAR scan file not found: {bin_path}")

        lbl_path = None
        if label_path is not None:
            lp = Path(label_path)
            if not lp.is_absolute():
                lp = PROJECT_ROOT / lp
            if lp.is_file():
                lbl_path = lp

        if num_points <= 0:
            raise InvalidInputError(f"num_points must be strictly positive, got {num_points}")

        # Ensure model is loaded
        self.load_model()
        assert self.segmenter is not None

        try:
            with torch.inference_mode():
                # Reuses Member 1 inference pipeline
                raw_result = self.segmenter.predict_file(
                    bin_path=str(path),
                    label_path=str(lbl_path) if lbl_path else None,
                    interpolate_to_full=interpolate_to_full,
                )
        except Exception as e:
            raise InferenceError(f"LiDAR inference failed on frame '{path.name}': {e}")

        pts = raw_result["points"]  # (N, 4)
        preds = raw_result["predicted_labels"]  # (N,)
        confs = raw_result["confidence_scores"]  # (N,)
        frame_id = raw_result.get("frame_id", path.stem)
        total_points = len(pts)

        if total_points == 0:
            raise InvalidInputError("Point cloud contains zero points after preprocessing.")

        # Class distribution histogram
        unique_classes, counts = np.unique(preds, return_counts=True)
        class_dist: Dict[str, int] = {
            ID_TO_CLASS.get(int(cls_id), f"class_{cls_id}"): int(cnt)
            for cls_id, cnt in zip(unique_classes, counts)
        }

        # Spatial bounds
        spatial_bounds = {
            "min_x": round(float(np.min(pts[:, 0])), 4),
            "max_x": round(float(np.max(pts[:, 0])), 4),
            "min_y": round(float(np.min(pts[:, 1])), 4),
            "max_y": round(float(np.max(pts[:, 1])), 4),
            "min_z": round(float(np.min(pts[:, 2])), 4),
            "max_z": round(float(np.max(pts[:, 2])), 4),
        }

        # Confidence statistics
        confidence_info = {
            "mean": round(float(np.mean(confs)), 4),
            "min": round(float(np.min(confs)), 4),
            "max": round(float(np.max(confs)), 4),
            "std": round(float(np.std(confs)), 4),
        }

        # Downsample preview points if cloud is large
        preview_limit = min(preview_points_limit, total_points)
        if total_points > preview_limit:
            preview_indices = np.linspace(0, total_points - 1, preview_limit, dtype=int)
        else:
            preview_indices = np.arange(total_points, dtype=int)

        preview_points: List[Dict[str, Any]] = []
        gt_labels = raw_result.get("ground_truth_labels")

        for idx in preview_indices:
            p_lbl = int(preds[idx])
            pt_dict: Dict[str, Any] = {
                "x": round(float(pts[idx, 0]), 4),
                "y": round(float(pts[idx, 1]), 4),
                "z": round(float(pts[idx, 2]), 4),
                "intensity": round(float(pts[idx, 3]), 4) if pts.shape[1] > 3 else 0.0,
                "predicted_label": p_lbl,
                "class_name": ID_TO_CLASS.get(p_lbl, f"class_{p_lbl}"),
                "confidence": round(float(confs[idx]), 4),
                "ground_truth_label": int(gt_labels[idx]) if gt_labels is not None else None,
            }
            preview_points.append(pt_dict)

        # Optional evaluation info if authentic labels were provided
        eval_info = None
        if gt_labels is not None:
            valid_mask = (gt_labels >= 0) & (gt_labels < NUM_CLASSES)
            if np.any(valid_mask):
                correct = np.sum(preds[valid_mask] == gt_labels[valid_mask])
                acc = float(correct / np.sum(valid_mask)) * 100.0
                eval_info = {
                    "accuracy_percent": round(acc, 2),
                    "evaluated_points": int(np.sum(valid_mask)),
                }

        response_data: Dict[str, Any] = {
            "frame_id": frame_id,
            "total_points": int(total_points),
            "point_count": int(total_points),
            "device": str(self.device),
            "predicted_labels": [int(x) for x in preds],
            "confidence_scores": [round(float(x), 4) for x in confs],
            "points": [[round(float(coord), 4) for coord in pt] for pt in pts[:preview_limit]],
            "confidence_information": confidence_info,
            "class_distribution": class_dist,
            "spatial_bounds": spatial_bounds,
            "preview_points": preview_points,
            "evaluation_information": eval_info,
        }

        return to_json_safe(response_data)
