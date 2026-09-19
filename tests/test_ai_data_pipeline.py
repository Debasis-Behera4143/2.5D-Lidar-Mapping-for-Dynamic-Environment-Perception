"""
Comprehensive Unit and Integration Test Suite for LiDAR Adaptive Mapping AI/ML Module.

Tests:
1. LiDAR .bin loader (shape, dtypes, bounds, corruption handling)
2. SemanticKITTI .label loader (16-bit semantic and instance ID unpacking)
3. Label mapping and colorization (8-class project taxonomy, LUT indexing)
4. Preprocessor (NaN removal, range filtering, ROI cropping, sampling)
5. PyTorch Dataset and DataLoader batch generation
6. RandLA-Net architecture (forward pass, shape preservation, gradient flow)
7. Inference pipeline output contract verification
8. Evaluation metrics (Accuracy, Precision, Recall, Per-Class IoU, mIoU)
"""

import os
from pathlib import Path
import numpy as np
import pytest
import torch

from src.data.lidar_loader import LiDARLoader
from src.data.label_loader import LabelLoader
from src.data.sample_generator import generate_synthetic_kitti_frame, save_kitti_frame
from src.data.dataset import SemanticKITTIDataset, collate_pointcloud_batch
from src.preprocessing.preprocess import PointCloudPreprocessor
from src.ai.label_mapping import (
    PROJECT_CLASSES,
    NUM_CLASSES,
    map_raw_to_project_labels,
    colorize_mapped_labels,
    ID_TO_CLASS,
)
from src.ai.model import RandLANet, compute_knn
from src.ai.inference import SemanticSegmenter
from src.ai.evaluate import SegmentationEvaluator, evaluate_batch


@pytest.fixture(scope="session")
def sample_frame_paths(tmp_path_factory) -> tuple:
    """Fixture providing temporary .bin and .label files."""
    tmp_dir = tmp_path_factory.mktemp("kitti_test")
    bin_path = tmp_dir / "000000.bin"
    label_path = tmp_dir / "000000.label"

    pts, lbls = generate_synthetic_kitti_frame(num_points=1000, seed=123)
    save_kitti_frame(pts, lbls, bin_path, label_path)
    return bin_path, label_path, pts, lbls


# ============================================================================
# 1. LiDAR Loader Tests
# ============================================================================
def test_lidar_loader(sample_frame_paths):
    bin_path, _, ground_truth_pts, _ = sample_frame_paths

    points = LiDARLoader.load_bin(bin_path)
    assert isinstance(points, np.ndarray)
    assert points.dtype == np.float32
    assert points.ndim == 2
    assert points.shape[1] == 4
    assert len(points) == len(ground_truth_pts)

    stats = LiDARLoader.compute_statistics(points)
    assert stats["num_points"] == len(points)
    assert stats["shape"] == (len(points), 4)
    assert stats["has_nan"] is False
    assert stats["has_inf"] is False
    assert stats["x_min_max"][0] <= stats["x_min_max"][1]
    assert stats["y_min_max"][0] <= stats["y_min_max"][1]
    assert stats["z_min_max"][0] <= stats["z_min_max"][1]


def test_lidar_loader_missing_file():
    with pytest.raises(FileNotFoundError):
        LiDARLoader.load_bin("non_existent_file.bin")


def test_lidar_loader_corrupted_file(tmp_path):
    bad_file = tmp_path / "bad.bin"
    # Write 7 float32 bytes (not multiple of 16 bytes = 4 floats)
    bad_file.write_bytes(b"\x00" * 7)
    with pytest.raises(ValueError):
        LiDARLoader.load_bin(bad_file)


# ============================================================================
# 2. Label Loader Tests
# ============================================================================
def test_label_loader(sample_frame_paths):
    _, label_path, _, ground_truth_lbls = sample_frame_paths

    raw_labels, semantic_ids, instance_ids = LabelLoader.load_label(
        label_path, expected_points=len(ground_truth_lbls)
    )

    assert len(raw_labels) == len(ground_truth_lbls)
    assert raw_labels.dtype == np.uint32
    assert semantic_ids.dtype == np.uint16
    assert instance_ids.dtype == np.uint16

    # Verify bitwise unpacking
    expected_sem = (ground_truth_lbls & 0xFFFF).astype(np.uint16)
    expected_inst = (ground_truth_lbls >> 16).astype(np.uint16)
    np.testing.assert_array_equal(semantic_ids, expected_sem)
    np.testing.assert_array_equal(instance_ids, expected_inst)

    dist = LabelLoader.compute_label_distribution(semantic_ids, instance_ids)
    assert dist["total_labels"] == len(semantic_ids)
    assert dist["num_unique_classes"] > 0


# ============================================================================
# 3. Label Mapping Tests
# ============================================================================
def test_label_mapping():
    assert NUM_CLASSES == 8
    assert len(PROJECT_CLASSES) == 8

    # Test key mappings
    raw_test = np.array([
        40,   # road -> 0
        48,   # sidewalk -> 1
        50,   # building -> 2
        70,   # vegetation -> 3
        10,   # car -> 4 (vehicle)
        30,   # person -> 5 (pedestrian)
        80,   # pole -> 6 (pole_sign)
        0,    # unlabeled -> 7 (other)
        252,  # moving car -> 4 (vehicle)
    ], dtype=np.uint16)

    mapped = map_raw_to_project_labels(raw_test)
    assert mapped[0] == 0  # road
    assert mapped[1] == 1  # sidewalk
    assert mapped[2] == 2  # building
    assert mapped[3] == 3  # vegetation
    assert mapped[4] == 4  # vehicle
    assert mapped[5] == 5  # pedestrian
    assert mapped[6] == 6  # pole_sign
    assert mapped[7] == 7  # other
    assert mapped[8] == 4  # moving car -> vehicle

    # Test colorizer
    colors_f = colorize_mapped_labels(mapped, as_float=True)
    assert colors_f.shape == (len(mapped), 3)
    assert colors_f.dtype == np.float32
    assert np.all((colors_f >= 0.0) & (colors_f <= 1.0))


# ============================================================================
# 4. Preprocessing Tests
# ============================================================================
def test_preprocessing():
    pts = np.array([
        [10.0, 5.0, 0.0, 0.5],
        [np.nan, 1.0, 1.0, 0.1],     # NaN
        [0.0, 0.0, 0.0, 0.0],        # Origin
        [0.5, 0.5, 0.0, 0.2],        # Near (<1.5m)
        [100.0, 0.0, 0.0, 0.3],      # Far (>80m)
        [20.0, 2.0, -1.0, 0.8],      # Valid
    ], dtype=np.float32)
    lbls = np.arange(len(pts), dtype=np.int64)

    # 1. Invalid point removal
    clean_pts, clean_lbls, _ = PointCloudPreprocessor.remove_invalid_points(pts, lbls)
    assert len(clean_pts) == 4  # NaN and Origin removed

    # 2. Range filtering
    rng_pts, rng_lbls, _ = PointCloudPreprocessor.filter_by_range(clean_pts, clean_lbls, 1.5, 80.0)
    assert len(rng_pts) == 2    # Near and Far removed
    assert len(rng_lbls) == 2

    # 3. Sampling
    sampled_pts, sampled_lbls, _ = PointCloudPreprocessor.sample_points(
        rng_pts, rng_lbls, target_points=10, random_seed=42
    )
    assert len(sampled_pts) == 10
    assert len(sampled_lbls) == 10


# ============================================================================
# 5. PyTorch Dataset and DataLoader Tests
# ============================================================================
def test_dataset_pipeline():
    dataset = SemanticKITTIDataset(
        dataset_root="data/sample_kitti",
        sequences=["00"],
        target_num_points=512,
    )
    assert len(dataset) > 0

    item = dataset[0]
    assert "xyz" in item
    assert "features" in item
    assert "labels" in item
    assert "frame_id" in item

    assert item["xyz"].shape == (512, 3)
    assert item["features"].shape == (512, 4)
    assert item["labels"].shape == (512,)
    assert item["labels"].dtype == torch.int64

    # Test batch collate
    batch = collate_pointcloud_batch([dataset[0], dataset[0]])
    assert batch["xyz"].shape == (2, 512, 3)
    assert batch["features"].shape == (2, 4, 512)
    assert batch["labels"].shape == (2, 512)
    assert len(batch["frame_ids"]) == 2


# ============================================================================
# 6. RandLA-Net Model Tests
# ============================================================================
def test_randla_net_model():
    B, N, C_in = 2, 256, 4
    xyz = torch.randn(B, N, 3)
    features = torch.randn(B, C_in, N)

    model = RandLANet(num_classes=8, in_channels=C_in, k_neighbors=8)
    model.eval()

    with torch.no_grad():
        logits = model(xyz, features)

    assert logits.shape == (B, 8, N)

    # Test backward pass / gradient flow
    model.train()
    logits_train = model(xyz, features)
    dummy_labels = torch.randint(0, 8, (B, N))
    loss = torch.nn.functional.cross_entropy(logits_train, dummy_labels)
    loss.backward()

    # Check gradients exist
    grad_norm = sum(p.grad.norm().item() for p in model.parameters() if p.grad is not None)
    assert grad_norm > 0.0


# ============================================================================
# 7. Inference Output Contract Tests
# ============================================================================
def test_inference_output_contract():
    segmenter = SemanticSegmenter(num_points=512)
    dummy_points = np.random.uniform(-20.0, 20.0, size=(1000, 4)).astype(np.float32)

    result = segmenter.predict_points(dummy_points, frame_id="test_frame_01")

    # Verify keys
    expected_keys = {"points", "predicted_labels", "confidence_scores", "frame_id"}
    assert set(result.keys()) == expected_keys

    # Verify types
    assert isinstance(result["points"], np.ndarray)
    assert isinstance(result["predicted_labels"], np.ndarray)
    assert isinstance(result["confidence_scores"], np.ndarray)
    assert isinstance(result["frame_id"], str)

    # Verify shapes and bounds
    N = len(result["points"])
    assert N == 512
    assert result["predicted_labels"].shape == (N,)
    assert result["confidence_scores"].shape == (N,)
    assert result["frame_id"] == "test_frame_01"

    # Verify value ranges
    assert np.all((result["predicted_labels"] >= 0) & (result["predicted_labels"] < 8))
    assert np.all((result["confidence_scores"] >= 0.0) & (result["confidence_scores"] <= 1.0))


# ============================================================================
# 8. Evaluation Metrics Tests
# ============================================================================
def test_evaluation_metrics():
    # Construct exact known confusion matrix
    # True classes:  [0, 0, 1, 1, 2]
    # Pred classes:  [0, 1, 1, 1, 2]
    # Class 0: TP=1, FP=0, FN=1 -> Prec = 1.0, Rec = 0.5, IoU = 1/2 = 0.5
    # Class 1: TP=2, FP=1, FN=0 -> Prec = 2/3, Rec = 1.0, IoU = 2/3 ≈ 0.667
    # Class 2: TP=1, FP=0, FN=0 -> Prec = 1.0, Rec = 1.0, IoU = 1.0
    y_true = np.array([0, 0, 1, 1, 2], dtype=np.int64)
    y_pred = np.array([0, 1, 1, 1, 2], dtype=np.int64)

    evaluator = SegmentationEvaluator(num_classes=8)
    evaluator.update(y_true, y_pred)
    metrics = evaluator.compute_metrics()

    # Overall Accuracy: 4/5 = 0.8
    assert np.isclose(metrics["overall_accuracy"], 4.0 / 5.0)

    # Class 0 IoU
    assert np.isclose(metrics["per_class_iou"]["road"], 0.5)
    # Class 1 IoU
    assert np.isclose(metrics["per_class_iou"]["sidewalk"], 2.0 / 3.0)
    # Class 2 IoU
    assert np.isclose(metrics["per_class_iou"]["building"], 1.0)

    # Mean IoU over classes present (classes 0, 1, 2)
    expected_miou = (0.5 + 2.0 / 3.0 + 1.0) / 3.0
    assert np.isclose(metrics["mean_iou"], expected_miou)


# ============================================================================
# 9. Real SemanticKITTI Dataset Loading Tests
# ============================================================================
def test_real_semantic_kitti_dataset():
    real_root = Path("data/semantic_kitti")
    if not (real_root / "sequences" / "00" / "velodyne" / "000000.bin").is_file():
        pytest.skip("Real SemanticKITTI dataset not present on local machine.")

    from src.data.dataset import create_dataloader

    loader = create_dataloader(
        dataset_root=real_root,
        sequences=["00"],
        split="all",
        batch_size=1,
        target_num_points=1024,
    )

    assert len(loader.dataset) >= 1
    batch = next(iter(loader))
    assert batch["xyz"].shape == (1, 1024, 3)
    assert batch["features"].shape == (1, 4, 1024)
    assert batch["labels"].shape == (1, 1024)
    assert "00_000000" in batch["frame_ids"][0]


def test_zero_data_leakage_on_sample_dataset():
    """Verify that train and validation datasets have 0 overlapping frames."""
    from src.data.dataset import get_train_val_loaders

    train_loader, val_loader = get_train_val_loaders(
        dataset_root="data/sample_kitti",
        train_sequences=["00"],
        val_sequences=["00"],
        batch_size=1,
        target_num_points=512,
    )

    train_frames = {item["frame_id"] for item in train_loader.dataset}
    val_frames = {item["frame_id"] for item in val_loader.dataset}

    assert len(train_frames) > 0
    assert len(val_frames) > 0
    # Zero leakage assertion
    overlap = train_frames.intersection(val_frames)
    assert len(overlap) == 0, f"Data leakage detected! Overlapping frames: {overlap}"


# ============================================================================
# 10. Visual Verification & Error Map Test
# ============================================================================
def test_visual_verification_and_error_map(tmp_path):
    from src.visualization.pointcloud_viewer import PointCloudVisualizer

    pts = np.random.uniform(-10.0, 10.0, size=(100, 4)).astype(np.float32)
    gt = np.array([0] * 50 + [1] * 50, dtype=np.int64)
    pred = np.array([0] * 40 + [1] * 10 + [1] * 30 + [2] * 20, dtype=np.int64)

    out = PointCloudVisualizer.compare_ground_truth_vs_prediction(
        points=pts,
        gt_labels=gt,
        pred_labels=pred,
        save_dir=tmp_path,
        frame_id="test_compare",
        headless=True,
    )

    assert out["total_points"] == 100
    assert out["correct_points"] == 70  # 40 in class 0 + 30 in class 1
    assert out["misclassified_points"] == 30
    assert np.isclose(out["accuracy"], 70.0)

    assert Path(out["gt_ply"]).is_file()
    assert Path(out["pred_ply"]).is_file()
    assert Path(out["error_ply"]).is_file()


# ============================================================================
# 11. Full-Cloud Dense Interpolation Contract Tests
# ============================================================================
def test_interpolate_to_full_contract():
    segmenter = SemanticSegmenter(num_points=256)
    x = np.random.uniform(-15.0, 15.0, size=800).astype(np.float32)
    y = np.random.uniform(-15.0, 15.0, size=800).astype(np.float32)
    z = np.random.uniform(-1.5, 1.5, size=800).astype(np.float32)
    intensity = np.random.uniform(0.1, 0.9, size=800).astype(np.float32)
    # Ensure range >= 2.0m
    dist_xy = np.sqrt(x**2 + y**2)
    x[dist_xy < 2.0] += 3.0
    pts = np.column_stack([x, y, z, intensity])

    result = segmenter.predict_points(pts, frame_id="dense_test", interpolate_to_full=True)

    assert "points" in result
    assert "predicted_labels" in result
    assert "confidence_scores" in result
    assert len(result["points"]) == len(pts)
    assert len(result["predicted_labels"]) == len(pts)
    assert len(result["confidence_scores"]) == len(pts)
    assert np.all((result["predicted_labels"] >= 0) & (result["predicted_labels"] < 8))
    assert np.all((result["confidence_scores"] >= 0.0) & (result["confidence_scores"] <= 1.0))


# ============================================================================
# 12. Synchronized Point-Label Alignment Tests
# ============================================================================
def test_synchronized_label_processing():
    segmenter = SemanticSegmenter(num_points=128)
    x = np.random.uniform(-15.0, 15.0, size=500).astype(np.float32)
    y = np.random.uniform(-15.0, 15.0, size=500).astype(np.float32)
    z = np.random.uniform(-1.5, 1.5, size=500).astype(np.float32)
    intensity = np.random.uniform(0.1, 0.9, size=500).astype(np.float32)
    dist_xy = np.sqrt(x**2 + y**2)
    x[dist_xy < 2.0] += 3.0
    pts = np.column_stack([x, y, z, intensity])
    labels = np.random.randint(0, 8, size=500, dtype=np.int64)

    # Downsampled synchronized processing
    result_down = segmenter.predict_points(pts, labels=labels, frame_id="sync_down", interpolate_to_full=False)
    assert "ground_truth_labels" in result_down
    assert len(result_down["points"]) == len(result_down["ground_truth_labels"])

    # Dense synchronized processing
    result_dense = segmenter.predict_points(pts, labels=labels, frame_id="sync_dense", interpolate_to_full=True)
    assert "ground_truth_labels" in result_dense
    assert len(result_dense["points"]) == len(result_dense["ground_truth_labels"])
    assert len(result_dense["points"]) == len(pts)


# ============================================================================
# 13. Type Annotation Integrity Tests (Python 3.14 PEP 649)
# ============================================================================
def test_type_annotations_integrity():
    import inspect
    import importlib
    import pkgutil
    import src

    for mod_info in pkgutil.walk_packages(src.__path__, "src."):
        mod = importlib.import_module(mod_info.name)
        for name, obj in inspect.getmembers(mod):
            if inspect.isfunction(obj) or inspect.isclass(obj):
                # Evaluating __annotations__ will raise NameError if unimported typing is used
                _ = getattr(obj, "__annotations__", None)

