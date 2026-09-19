"""
SemanticKITTI label (.label) loader.

Decodes uint32 binary labels into lower 16-bit semantic class IDs
and upper 16-bit instance tracking IDs.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import numpy as np


class LabelLoader:
    """
    Loader and decoder for SemanticKITTI .label files.
    """

    @staticmethod
    def load_label(
        file_path: Union[str, Path],
        expected_points: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Load and unpack a SemanticKITTI .label file.

        SemanticKITTI label binary format:
        - 32-bit unsigned integers (uint32)
        - Lower 16 bits (label & 0xFFFF): Semantic Class ID
        - Upper 16 bits (label >> 16): Instance ID

        Args:
            file_path: Path to .label file.
            expected_points: If provided, asserts number of labels matches points.

        Returns:
            Tuple of:
                - raw_labels: (N,) uint32 full binary labels
                - semantic_ids: (N,) uint16 unpacked semantic IDs
                - instance_ids: (N,) uint16 unpacked instance IDs

        Raises:
            FileNotFoundError: If file not found.
            ValueError: If expected_points does not match label count.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Label file not found: {path.resolve()}")

        raw_labels = np.fromfile(str(path), dtype=np.uint32)

        if expected_points is not None and len(raw_labels) != expected_points:
            raise ValueError(
                f"Label count mismatch: file has {len(raw_labels)} labels, "
                f"but point cloud has {expected_points} points."
            )

        # Unpack lower 16 bits for semantic label
        semantic_ids = (raw_labels & 0xFFFF).astype(np.uint16)
        # Unpack upper 16 bits for instance label
        instance_ids = (raw_labels >> 16).astype(np.uint16)

        return raw_labels, semantic_ids, instance_ids

    @staticmethod
    def compute_label_distribution(
        semantic_ids: np.ndarray,
        instance_ids: Optional[np.ndarray] = None,
    ) -> Dict[str, Union[int, Dict[int, int]]]:
        """
        Compute frequency distribution of semantic classes and instances.
        """
        unique_classes, counts = np.unique(semantic_ids, return_counts=True)
        class_distribution = {int(cls): int(cnt) for cls, cnt in zip(unique_classes, counts)}

        stats: Dict[str, Union[int, Dict[int, int]]] = {
            "total_labels": int(len(semantic_ids)),
            "num_unique_classes": int(len(unique_classes)),
            "class_distribution": class_distribution,
        }

        if instance_ids is not None:
            unique_instances = np.unique(instance_ids[instance_ids > 0])
            stats["num_unique_instances"] = int(len(unique_instances))

        return stats

    @classmethod
    def print_label_summary(
        cls,
        file_path: Union[str, Path],
        expected_points: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Load label file and print human-readable summary.
        """
        path = Path(file_path)
        raw, sem, inst = cls.load_label(path, expected_points=expected_points)
        stats = cls.compute_label_distribution(sem, inst)

        print("=" * 60)
        print(f"Label File Summary: {path.name}")
        print("=" * 60)
        print(f"Total Labels:        {stats['total_labels']:,}")
        print(f"Unique Semantic IDs: {stats['num_unique_classes']}")
        if "num_unique_instances" in stats:
            print(f"Unique Instances:    {stats['num_unique_instances']}")
        print("Semantic ID Counts:")
        for sem_id, count in sorted(stats["class_distribution"].items()):
            pct = 100.0 * count / len(sem)
            print(f"  ID {sem_id:>3d}: {count:>8,d} points ({pct:>5.1f}%)")
        print("=" * 60)

        return raw, sem, inst


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect a SemanticKITTI .label file.")
    parser.add_argument("label_path", type=str, nargs="?", default=None, help="Path to .label file")
    args = parser.parse_args()

    if args.label_path:
        LabelLoader.print_label_summary(args.label_path)
    else:
        default_sample = Path("data/sample_kitti/sequences/00/labels/000000.label")
        if default_sample.is_file():
            LabelLoader.print_label_summary(default_sample)
        else:
            print("No .label file provided. Usage: python -m src.data.label_loader <path/to/frame.label>")
