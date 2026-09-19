# Member 1 Cleanup & Stabilization Changelog

**Project:** SIH 2026 — Adaptive Variable-Resolution 2.5D LiDAR Mapping for Dynamic Environment Perception  
**Role:** Member 1 (AI/ML & LiDAR Data Engineering)  
**Date:** September 13, 2026  

---

## 1. Type Annotation and Import Fixes (Python 3.14 PEP 649)
- **`src/ai/evaluate.py`:** Added `Any` to `from typing import ...`. Fixed deferred annotation evaluation `NameError` on `compute_metrics` and `evaluate_batch`.
- **`src/ai/train.py`:** Added `Any` to `from typing import ...` and updated `validate_epoch` return type from `Dict[str, any]` to `Dict[str, Any]`.
- **`src/visualization/pointcloud_viewer.py`:** Added `Any, Dict` to `from typing import ...`. Fixed deferred annotation evaluation `NameError` on `compare_ground_truth_vs_prediction`.
- **Verified with Introspection Test:** Added `test_type_annotations_integrity` in `tests/test_ai_data_pipeline.py` verifying all public modules and classes evaluate `__annotations__` without `NameError`.

---

## 2. Spatial-Semantic Ground Truth Alignment Fix
- **Problem:** `pointcloud_viewer.py` previously sliced `raw_sem[:len(sampled_pts)]` from the raw uncleaned scan, resulting in completely scrambled ground truth labels relative to preprocessed, range-filtered, ROI-cropped 3D coordinates.
- **Fix:** Implemented synchronized preprocessing in `SemanticSegmenter.predict_points(points, labels=...)`. Points and ground truth labels are now processed simultaneously through identical spatial filtering and random sampling masks.
- **Verification:** The 3-way visual verification now aligns 3D points and ground-truth labels 1:1, reporting authentic classification accuracy ($\approx 2.59\%$).

---

## 3. Full-Cloud Dense Label Interpolation (`interpolate_to_full`)
- **Problem:** `SemanticSegmenter` previously only produced downsampled predictions ($N \approx 2048-4096$). Member 2 (Adaptive-Grid Mapping) requires dense points (~120k) to populate elevation and occupancy grids.
- **Fix:** Implemented memory-safe 1-NN KDTree interpolation via `scipy.spatial.cKDTree` in `src/ai/inference.py`. When `interpolate_to_full=True`, the model runs forward inference on sampled points, and predictions/confidences are efficiently propagated back to all cleaned points in $O(N \log M)$ time.
- **Test:** Added `test_interpolate_to_full_contract` in `tests/test_ai_data_pipeline.py`.

---

## 4. Dataset Deduplication & Train/Val Leakage Resolution
- **Problem:** Sequence 08 (`data/semantic_kitti/sequences/08/`) was a bit-for-bit duplicate of Sequence 00 (SHA256: `92E945F3...`), creating 100% train/val data leakage.
- **Fix:** Deleted duplicate sequence 08 (`velodyne/000000.bin` and `labels/000000.label`). Retained authentic Sequence 00 Frame 000000.
- **Defensive Slicing:** Updated `src/data/dataset.py` `_index_dataset` to handle available sequences defensively.
- **Zero-Leakage Test:** Added `test_zero_data_leakage_on_sample_dataset` verifying that train and validation loaders have 0 overlapping frames.

---

## 5. Directory Hygiene & Artifact Reorganization
- **Separated Runtime Outputs from Data:** Moved generated `.ply` point cloud visualizations from `data/visualizations/` into `data/outputs/visualizations/`.
- **Output Default:** Updated `PointCloudVisualizer.compare_ground_truth_vs_prediction` default save directory to `data/outputs/visualizations/`.

---

## 6. Member 2 Handoff Documentation
- Created [`docs/MEMBER2_HANDOFF_GUIDE.md`](MEMBER2_HANDOFF_GUIDE.md) detailing:
  - Perception output contract schema.
  - Recommended cell resolutions per class.
  - Coordinate system conventions.
  - Complete quickstart code examples.
  - Honest disclosure of baseline checkpoint performance (2.45% accuracy).
