"""
Evaluation Metrics for Point Cloud Semantic Segmentation.

Computes mathematically rigorous metrics from true confusion matrix:
- Overall Accuracy (OA)
- Per-class and Macro Precision
- Per-class and Macro Recall
- Per-class Intersection over Union (IoU)
- Mean Intersection over Union (mIoU)
- Formatted metrics report and confusion matrix
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch

from src.ai.label_mapping import ID_TO_CLASS, NUM_CLASSES, PROJECT_CLASSES


class SegmentationEvaluator:
    """
    Online confusion matrix accumulator and metric computer for semantic segmentation.
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        class_names: Optional[List[str]] = None,
        ignore_index: Optional[int] = None,
    ):
        self.num_classes = num_classes
        self.class_names = class_names or PROJECT_CLASSES
        self.ignore_index = ignore_index
        self.reset()

    def reset(self) -> None:
        """Reset internal confusion matrix."""
        # confusion_matrix[true_class, pred_class]
        self.confusion_matrix = np.zeros((self.num_classes, self.num_classes), dtype=np.int64)

    def update(self, y_true: Union[np.ndarray, torch.Tensor], y_pred: Union[np.ndarray, torch.Tensor]) -> None:
        """
        Accumulate batch predictions and ground truth into confusion matrix.

        Args:
            y_true: (N,) or (B, N) ground truth label array.
            y_pred: (N,) or (B, N) predicted label array.
        """
        if isinstance(y_true, torch.Tensor):
            y_true = y_true.detach().cpu().numpy()
        if isinstance(y_pred, torch.Tensor):
            y_pred = y_pred.detach().cpu().numpy()

        y_true = y_true.flatten()
        y_pred = y_pred.flatten()

        if len(y_true) != len(y_pred):
            raise ValueError(f"Length mismatch: y_true {len(y_true)} != y_pred {len(y_pred)}")

        # Filter out invalid or negative labels
        valid_mask = (y_true >= 0) & (y_true < self.num_classes) & (y_pred >= 0) & (y_pred < self.num_classes)
        t = y_true[valid_mask].astype(np.int64)
        p = y_pred[valid_mask].astype(np.int64)

        # Fast 2D bincount accumulation
        encoded = t * self.num_classes + p
        counts = np.bincount(encoded, minlength=self.num_classes ** 2)
        self.confusion_matrix += counts.reshape(self.num_classes, self.num_classes)

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Compute precision, recall, IoU, and accuracy from confusion matrix.

        Returns:
            Dictionary of computed metrics.
        """
        cm = self.confusion_matrix
        total_points = np.sum(cm)

        if total_points == 0:
            return {
                "overall_accuracy": 0.0,
                "mean_iou": 0.0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "per_class_iou": {name: 0.0 for name in self.class_names},
                "per_class_precision": {name: 0.0 for name in self.class_names},
                "per_class_recall": {name: 0.0 for name in self.class_names},
                "class_support": {name: 0 for name in self.class_names},
                "confusion_matrix": cm,
            }

        # True Positives: diagonal
        tp = np.diag(cm).astype(np.float64)
        # False Positives: column sum - diagonal
        fp = (np.sum(cm, axis=0) - tp).astype(np.float64)
        # False Negatives: row sum - diagonal
        fn = (np.sum(cm, axis=1) - tp).astype(np.float64)
        # Support: total points per class in ground truth
        support = np.sum(cm, axis=1)

        # Overall Accuracy (evaluated across all points or non-ignored points)
        if self.ignore_index is not None and 0 <= self.ignore_index < self.num_classes:
            valid_pts_mask = np.ones(self.num_classes, dtype=bool)
            valid_pts_mask[self.ignore_index] = False
            total_eval_points = np.sum(cm[valid_pts_mask, :])
            oa = float(np.sum(tp[valid_pts_mask]) / max(1.0, total_eval_points))
        else:
            oa = float(np.sum(tp) / total_points)

        # Per-class IoU = TP / (TP + FP + FN)
        iou_denom = tp + fp + fn
        per_class_iou = np.zeros(self.num_classes, dtype=np.float64)
        valid_iou = iou_denom > 0
        per_class_iou[valid_iou] = tp[valid_iou] / iou_denom[valid_iou]

        # Per-class Precision = TP / (TP + FP)
        prec_denom = tp + fp
        per_class_prec = np.zeros(self.num_classes, dtype=np.float64)
        valid_prec = prec_denom > 0
        per_class_prec[valid_prec] = tp[valid_prec] / prec_denom[valid_prec]

        # Per-class Recall = TP / (TP + FN)
        rec_denom = tp + fn
        per_class_rec = np.zeros(self.num_classes, dtype=np.float64)
        valid_rec = rec_denom > 0
        per_class_rec[valid_rec] = tp[valid_rec] / rec_denom[valid_rec]

        # Mean IoU calculation
        classes_to_include = support > 0
        if self.ignore_index is not None and 0 <= self.ignore_index < self.num_classes:
            classes_to_include[self.ignore_index] = False

        if np.any(classes_to_include):
            mean_iou = float(np.mean(per_class_iou[classes_to_include]))
            macro_prec = float(np.mean(per_class_prec[classes_to_include]))
            macro_rec = float(np.mean(per_class_rec[classes_to_include]))
        else:
            mean_iou = 0.0
            macro_prec = 0.0
            macro_rec = 0.0

        return {
            "overall_accuracy": oa,
            "mean_iou": mean_iou,
            "macro_precision": macro_prec,
            "macro_recall": macro_rec,
            "per_class_iou": {name: float(per_class_iou[i]) for i, name in enumerate(self.class_names)},
            "per_class_precision": {name: float(per_class_prec[i]) for i, name in enumerate(self.class_names)},
            "per_class_recall": {name: float(per_class_rec[i]) for i, name in enumerate(self.class_names)},
            "class_support": {name: int(support[i]) for i, name in enumerate(self.class_names)},
            "confusion_matrix": cm,
        }

    def print_confusion_matrix(self) -> None:
        """Print a nicely formatted confusion matrix."""
        cm = self.confusion_matrix
        print("\n--- CONFUSION MATRIX [Rows: Ground Truth, Cols: Prediction] ---")
        header = "       " + "".join(f"{name[:7]:>8}" for name in self.class_names)
        print(header)
        print("-" * len(header))
        for i, name in enumerate(self.class_names):
            row_str = f"{name[:6]:<7}" + "".join(f"{cm[i, j]:>8d}" for j in range(self.num_classes))
            print(row_str)
        print("-" * len(header) + "\n")

    def print_report(self, show_confusion_matrix: bool = False) -> None:
        """Print a formatted metrics table."""
        metrics = self.compute_metrics()

        print("\n" + "=" * 75)
        print("SEMANTIC SEGMENTATION EVALUATION REPORT")
        print("=" * 75)
        print(f"{'Class ID':<9} {'Class Name':<14} {'Precision':<12} {'Recall':<12} {'IoU':<12} {'Support':<10}")
        print("-" * 75)

        for i, name in enumerate(self.class_names):
            prec = metrics["per_class_precision"][name] * 100
            rec = metrics["per_class_recall"][name] * 100
            iou = metrics["per_class_iou"][name] * 100
            supp = metrics["class_support"][name]
            flag = " (Ignored)" if self.ignore_index == i else ""
            print(f"{i:<9} {name + flag:<14} {prec:>9.2f}% {rec:>9.2f}% {iou:>9.2f}% {supp:>10,d}")

        print("-" * 75)
        print(f"Overall Accuracy:  {metrics['overall_accuracy'] * 100:.2f}%")
        print(f"Mean IoU (mIoU):   {metrics['mean_iou'] * 100:.2f}%")
        print(f"Macro Precision:   {metrics['macro_precision'] * 100:.2f}%")
        print(f"Macro Recall:      {metrics['macro_recall'] * 100:.2f}%")
        print("=" * 75)

        if show_confusion_matrix:
            self.print_confusion_matrix()


def evaluate_batch(
    y_true: Union[np.ndarray, torch.Tensor],
    y_pred: Union[np.ndarray, torch.Tensor],
) -> Dict[str, Any]:
    """Helper to evaluate a single pair of ground truth and predictions."""
    evaluator = SegmentationEvaluator()
    evaluator.update(y_true, y_pred)
    return evaluator.compute_metrics()


if __name__ == "__main__":
    # Test evaluation module with known ground truth and predictions
    y_true = np.array([0, 0, 0, 1, 1, 2, 2, 3, 4, 5, 6, 7], dtype=np.int64)
    # Simulated prediction with some correct and some swapped classes
    y_pred = np.array([0, 0, 1, 1, 1, 2, 0, 3, 4, 5, 6, 7], dtype=np.int64)

    evaluator = SegmentationEvaluator()
    evaluator.update(y_true, y_pred)
    evaluator.print_report()
