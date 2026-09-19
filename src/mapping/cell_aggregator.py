"""
Reusable point aggregation logic for 2.5D grid cells.

Calculates point counts, elevation statistics (min, max, mean, variance),
semantic class histograms, dominant class with deterministic tie-breaking,
mean confidence, and semantic purity.
"""

from typing import Any, Dict, Sequence, Union
import numpy as np


class CellAggregator:
    """Aggregates geometric elevation and semantic attributes for points within a grid cell."""

    @staticmethod
    def aggregate(
        z_coords: Union[np.ndarray, Sequence[float]],
        labels: Union[np.ndarray, Sequence[int]],
        confidences: Union[np.ndarray, Sequence[float]],
    ) -> Dict[str, Any]:
        """
        Aggregate a set of points in a cell into summary statistics.

        Args:
            z_coords: 1D array or sequence of Z coordinates (elevation).
            labels: 1D array or sequence of class IDs in [0, 7].
            confidences: 1D array or sequence of confidence scores in [0.0, 1.0].

        Returns:
            Dictionary containing:
            - point_count: int
            - min_height: float
            - max_height: float
            - mean_height: float
            - height_variance: float
            - dominant_class: int (smallest class ID on tie)
            - class_histogram: Dict[str, int]
            - mean_confidence: float
            - semantic_purity: float
        """
        z_arr = np.asarray(z_coords, dtype=np.float32)
        lbl_arr = np.asarray(labels, dtype=np.int64)
        conf_arr = np.asarray(confidences, dtype=np.float32)

        point_count = len(z_arr)
        if point_count == 0:
            raise ValueError("Cannot aggregate empty point collection (point_count must be > 0)")

        if len(lbl_arr) != point_count or len(conf_arr) != point_count:
            raise ValueError(
                f"Dimension mismatch: z ({point_count}), labels ({len(lbl_arr)}), confidences ({len(conf_arr)})"
            )

        # Height statistics
        min_h = float(np.min(z_arr))
        max_h = float(np.max(z_arr))
        mean_h = float(np.mean(z_arr))
        var_h = float(np.var(z_arr)) if point_count > 1 else 0.0

        # Confidence statistics
        mean_conf = float(np.mean(conf_arr))

        # Class histogram calculation
        classes, counts = np.unique(lbl_arr, return_counts=True)
        class_histogram: Dict[str, int] = {str(int(c)): int(cnt) for c, cnt in zip(classes, counts)}

        # Deterministic tie-breaking for dominant class:
        # If two or more classes share the max count, select the smallest class ID.
        max_count = -1
        dominant_class = -1
        # Sort classes ascending to guarantee smallest class ID wins on equal counts
        sorted_indices = np.argsort(classes)
        for idx in sorted_indices:
            cls_id = int(classes[idx])
            cnt = int(counts[idx])
            if cnt > max_count:
                max_count = cnt
                dominant_class = cls_id
            # If cnt == max_count, do not overwrite since classes are sorted ascending

        # Semantic purity: dominant class count / total points
        purity = float(max_count / point_count)

        return {
            "point_count": int(point_count),
            "min_height": round(min_h, 4),
            "max_height": round(max_h, 4),
            "mean_height": round(mean_h, 4),
            "height_variance": round(var_h, 6),
            "dominant_class": int(dominant_class),
            "class_histogram": class_histogram,
            "mean_confidence": round(mean_conf, 4),
            "semantic_purity": round(purity, 4),
        }
