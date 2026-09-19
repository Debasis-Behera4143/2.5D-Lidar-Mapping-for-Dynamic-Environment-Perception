"""
SemanticKITTI PyTorch Dataset and DataLoader Pipeline.

Provides indexed sequence dataset handling, point-label synchronization,
preprocessing, 8-class taxonomy mapping, and tensor batching.
"""

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

from src.data.lidar_loader import LiDARLoader
from src.data.label_loader import LabelLoader
from src.ai.label_mapping import map_raw_to_project_labels, NUM_CLASSES
from src.preprocessing.preprocess import PointCloudPreprocessor


class SemanticKITTIDataset(Dataset):
    """
    PyTorch Dataset for SemanticKITTI point cloud sequences.
    """

    def __init__(
        self,
        dataset_root: Union[str, Path],
        sequences: Optional[List[str]] = None,
        split: str = "train",
        split_ratio: float = 0.7,
        target_num_points: int = 8192,
        preprocessor: Optional[PointCloudPreprocessor] = None,
        has_labels: bool = True,
        augment: bool = False,
    ):
        """
        Args:
            dataset_root: Root directory containing 'sequences/<seq_id>/velodyne'
            sequences: List of sequence IDs to load (e.g., ['00', '08']). If None, auto-splits based on split.
            split: 'train', 'val', 'test', or 'all'.
            split_ratio: Ratio for frame-level splitting when single sequence is used.
            target_num_points: Number of points to sample per frame for PyTorch batching.
            preprocessor: PointCloudPreprocessor instance.
            has_labels: If True, searches for and loads corresponding .label files.
            augment: If True, applies random yaw rotation and jittering.
        """
        self.root = Path(dataset_root)
        self.split = split.lower()
        self.split_ratio = split_ratio
        self.target_num_points = target_num_points
        self.has_labels = has_labels
        self.augment = augment

        if preprocessor is not None:
            self.preprocessor = preprocessor
        else:
            self.preprocessor = PointCloudPreprocessor(
                min_range=1.5,
                max_range=60.0,
                roi_bounds=(-40.0, 40.0, -40.0, 40.0, -3.0, 4.0),
                target_num_points=target_num_points,
            )

        # Index frame paths
        self.frames: List[Dict[str, Union[str, Path]]] = []
        self._index_dataset(sequences)

    def _index_dataset(self, sequences: Optional[List[str]]) -> None:
        seq_dir = self.root / "sequences"
        if not seq_dir.is_dir():
            # Auto-check if semantic_kitti subdirectory exists inside root
            if (self.root / "semantic_kitti" / "sequences").is_dir():
                seq_dir = self.root / "semantic_kitti" / "sequences"
            elif (self.root / "velodyne").is_dir():
                available_seqs = [self.root]
                seq_dir = None
            else:
                raise FileNotFoundError(f"SemanticKITTI sequences directory not found at: {self.root.resolve()}")
        
        if seq_dir is not None:
            all_seq_dirs = sorted([p for p in seq_dir.iterdir() if p.is_dir()])
            seq_names = [p.name for p in all_seq_dirs]

            if sequences is None:
                # If sequence 08 exists, follow official benchmark split: 08 for val, others for train
                if "08" in seq_names and len(seq_names) > 1:
                    if self.split in ["val", "validation"]:
                        available_seqs = [seq_dir / "08"]
                    elif self.split == "train":
                        available_seqs = [seq_dir / s for s in seq_names if s != "08"]
                    else:
                        available_seqs = all_seq_dirs
                else:
                    available_seqs = all_seq_dirs
            else:
                available_seqs = [seq_dir / s for s in sequences if (seq_dir / s).is_dir()]
                if not available_seqs:
                    raise FileNotFoundError(
                        f"None of requested sequences {sequences} found in: {seq_dir.resolve()}"
                    )

        for seq in available_seqs:
            velo_dir = seq / "velodyne"
            labels_dir = seq / "labels"

            if not velo_dir.is_dir():
                continue

            bin_files = sorted(list(velo_dir.glob("*.bin")))
            for bin_file in bin_files:
                frame_stem = bin_file.stem
                seq_name = seq.name
                entry: Dict[str, Union[str, Path]] = {
                    "seq": seq_name,
                    "frame_id": f"{seq_name}_{frame_stem}",
                    "bin_path": bin_file,
                }

                if self.has_labels:
                    label_file = labels_dir / f"{frame_stem}.label"
                    if label_file.is_file():
                        entry["label_path"] = label_file
                    else:
                        entry["label_path"] = None

                self.frames.append(entry)

        # Frame-level split if single sequence loaded with multiple frames
        if sequences is not None and len(sequences) == 1 and len(self.frames) > 1:
            split_point = max(1, int(len(self.frames) * self.split_ratio))
            if self.split == "train":
                self.frames = self.frames[:split_point]
            elif self.split in ["val", "validation"]:
                self.frames = self.frames[split_point:]

        if len(self.frames) == 0:
            raise RuntimeError(f"No LiDAR .bin frames discovered for split '{self.split}' in {self.root.resolve()}")

    def __len__(self) -> int:
        return len(self.frames)

    def _augment_points(self, points: np.ndarray) -> np.ndarray:
        """Apply random yaw rotation and small jitter to XYZ."""
        angle = np.random.uniform(0.0, 2.0 * np.pi)
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rot_matrix = np.array([
            [cos_a, -sin_a, 0.0],
            [sin_a,  cos_a, 0.0],
            [0.0,    0.0,   1.0],
        ], dtype=np.float32)

        aug_pts = points.copy()
        aug_pts[:, :3] = aug_pts[:, :3] @ rot_matrix.T

        # Small Gaussian jitter on coordinates
        jitter = np.random.normal(0.0, 0.01, size=aug_pts[:, :3].shape).astype(np.float32)
        aug_pts[:, :3] += jitter
        return aug_pts

    def __getitem__(self, idx: int) -> Dict[str, Union[torch.Tensor, str]]:
        entry = self.frames[idx]

        # 1. Load raw points
        raw_points = LiDARLoader.load_bin(entry["bin_path"])

        # 2. Load labels if present
        if self.has_labels and entry.get("label_path") is not None:
            _, raw_sem_ids, _ = LabelLoader.load_label(entry["label_path"], expected_points=len(raw_points))
            mapped_labels = map_raw_to_project_labels(raw_sem_ids)
        else:
            mapped_labels = np.zeros(len(raw_points), dtype=np.int64)

        # 3. Preprocess and sample
        # Stochastic sampling for training; deterministic for validation
        seed = None if self.split == "train" else (42 + idx)
        processed_pts, processed_lbls = self.preprocessor.process(
            raw_points,
            mapped_labels,
            random_seed=seed,
        )

        # Ensure exact target point count
        if len(processed_pts) != self.target_num_points:
            processed_pts, processed_lbls, _ = PointCloudPreprocessor.sample_points(
                processed_pts,
                processed_lbls,
                target_points=self.target_num_points,
                random_seed=seed,
            )

        # 4. Augmentation
        if self.augment:
            processed_pts = self._augment_points(processed_pts)

        # 5. Build PyTorch tensors
        # XYZ coordinates: (N, 3)
        xyz_tensor = torch.from_numpy(processed_pts[:, :3]).float()
        # Features: (N, C) where C=4 [X, Y, Z, Intensity]
        feat_tensor = torch.from_numpy(processed_pts).float()
        # Labels: (N,) int64 in [0, 7]
        label_tensor = torch.from_numpy(processed_lbls).long()

        return {
            "xyz": xyz_tensor,
            "features": feat_tensor,
            "labels": label_tensor,
            "frame_id": str(entry["frame_id"]),
        }


def collate_pointcloud_batch(batch: List[Dict[str, Union[torch.Tensor, str]]]) -> Dict[str, Union[torch.Tensor, List[str]]]:
    """
    Collate individual point cloud dictionaries into a batched dictionary.

    Returns:
        - "xyz": (B, N, 3) float32
        - "features": (B, C, N) float32 (channels-first for 1D convolutions / PointNet / RandLA-Net)
        - "labels": (B, N) int64
        - "frame_ids": List of frame ID strings
    """
    xyz_batch = torch.stack([item["xyz"] for item in batch], dim=0)
    # Transpose features to (B, C, N) for PyTorch Conv1d layers
    feat_batch = torch.stack([item["features"].transpose(0, 1) for item in batch], dim=0)
    labels_batch = torch.stack([item["labels"] for item in batch], dim=0)
    frame_ids = [str(item["frame_id"]) for item in batch]

    return {
        "xyz": xyz_batch,
        "features": feat_batch,
        "labels": labels_batch,
        "frame_ids": frame_ids,
    }


def create_dataloader(
    dataset_root: Union[str, Path],
    sequences: Optional[List[str]] = None,
    split: str = "train",
    batch_size: int = 2,
    target_num_points: int = 4096,
    shuffle: Optional[bool] = None,
    num_workers: int = 0,
    augment: bool = False,
) -> DataLoader:
    """Helper to construct a ready-to-use DataLoader for a specific split."""
    if shuffle is None:
        shuffle = (split == "train")

    dataset = SemanticKITTIDataset(
        dataset_root=dataset_root,
        sequences=sequences,
        split=split,
        target_num_points=target_num_points,
        augment=augment,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_pointcloud_batch,
    )


def get_train_val_loaders(
    dataset_root: Union[str, Path],
    train_sequences: Optional[List[str]] = None,
    val_sequences: Optional[List[str]] = None,
    batch_size: int = 2,
    target_num_points: int = 4096,
    num_workers: int = 0,
) -> Tuple[DataLoader, DataLoader]:
    """Construct both training and validation loaders cleanly without data leakage."""
    train_loader = create_dataloader(
        dataset_root=dataset_root,
        sequences=train_sequences,
        split="train",
        batch_size=batch_size,
        target_num_points=target_num_points,
        shuffle=True,
        num_workers=num_workers,
        augment=True,
    )
    val_loader = create_dataloader(
        dataset_root=dataset_root,
        sequences=val_sequences,
        split="val",
        batch_size=batch_size,
        target_num_points=target_num_points,
        shuffle=False,
        num_workers=num_workers,
        augment=False,
    )
    return train_loader, val_loader



if __name__ == "__main__":
    loader = create_dataloader(
        dataset_root="data/sample_kitti",
        sequences=["00"],
        batch_size=2,
        target_num_points=4096,
    )

    for batch in loader:
        print("Dataset Pipeline Batch Verified:")
        print(f"  xyz shape:      {batch['xyz'].shape} (Expected: (B, N, 3))")
        print(f"  features shape: {batch['features'].shape} (Expected: (B, C, N))")
        print(f"  labels shape:   {batch['labels'].shape} (Expected: (B, N))")
        print(f"  frame_ids:      {batch['frame_ids']}")
        break
