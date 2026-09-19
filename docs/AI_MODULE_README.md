# AI/ML & LiDAR Data Engineering Module

**Role:** Member 1 — AI/ML and LiDAR Data Engineer  
**Project:** Adaptive Variable-Resolution 2.5D LiDAR Mapping for Dynamic Environment Perception  
**Dataset:** SemanticKITTI (Velodyne HDL-64E)

---

## 1. Overview & Architecture

This module implements the complete perception layer for our project. It ingests raw Velodyne LiDAR `.bin` files and SemanticKITTI `.label` files, performs spatial filtering and ROI cropping, maps classes to the unified 8-class project taxonomy, runs semantic segmentation via pure PyTorch RandLA-Net, and produces standardized output dictionaries for downstream 2.5D adaptive-grid mapping.

```text
  Raw LiDAR (.bin) + Labels (.label)
                  │
                  ▼
      [ LiDAR & Label Loaders ]
    (Unpack XYZ+Intensity & 16-bit IDs)
                  │
                  ▼
     [ Point Cloud Preprocessor ]
(NaN Removal, Range [1.5-60m], ROI Crop, Sampling)
                  │
                  ▼
      [ 8-Class Label Mapping ]
   (Road, Sidewalk, Building, Veg, ...)
                  │
                  ▼
    [ PyTorch RandLA-Net Model ]
 (LocSE + Attentive Pooling + Skip Upsample)
                  │
                  ▼
    [ Standard Perception Contract ]
  {points, labels, confidence, frame_id}
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
[Adaptive-Grid Mapping] [3D Visualizer / Export]
```

---

## 2. Standard Output Contract (For Team Members)

Whenever you call the inference pipeline or dataset loader, the output is formatted as follows:

```python
{
    "points": np.ndarray,            # Shape: (N, 4), dtype: float32 -> [X, Y, Z, Intensity]
    "predicted_labels": np.ndarray,  # Shape: (N,), dtype: int64   -> Class ID in [0, 7]
    "confidence_scores": np.ndarray, # Shape: (N,), dtype: float32 -> Softmax probability [0.0, 1.0]
    "frame_id": str                  # e.g., "000000" or "00_000000"
}
```

### Coordinate Frame Convention
- **X:** Forward (vehicle heading), in meters
- **Y:** Left, in meters
- **Z:** Up (height above sensor), in meters
- **Intensity:** Remission value in range $[0.0, 1.0]$

---

## 3. Project Taxonomy (8 Classes)

The raw SemanticKITTI classes (28+ raw IDs) are mapped into the following 8 classes:

| Class ID | Class Name | Included SemanticKITTI Classes | Color (RGB Float) | Recommended Grid Cell Resolution |
|---|---|---|---|---|
| **0** | `road` | road (40), parking (44), lane-marking (60) | `[0.50, 0.25, 0.50]` | Standard / Coarse (e.g. 0.4m) |
| **1** | `sidewalk` | sidewalk (48), other-ground (49) | `[0.96, 0.14, 0.59]` | Medium (e.g. 0.2m) |
| **2** | `building` | building (50), fence (51), structure (52) | `[0.35, 0.35, 0.35]` | Coarse (e.g. 0.5m) |
| **3** | `vegetation` | vegetation (70), trunk (71), terrain (72) | `[0.22, 0.60, 0.22]` | Medium (e.g. 0.3m) |
| **4** | `vehicle` | car (10), bicycle (11), truck (18), moving cars | `[0.20, 0.50, 0.90]` | **Fine / Dynamic** (e.g. 0.1m) |
| **5** | `pedestrian` | person (30), bicyclist (31), motorcyclist (32) | `[0.90, 0.15, 0.15]` | **Ultra-Fine / Critical** (e.g. 0.05m) |
| **6** | `pole_sign` | pole (80), traffic-sign (81), object (99) | `[1.00, 0.85, 0.10]` | Fine (e.g. 0.1m) |
| **7** | `other` | unlabeled (0), outlier (1), ground outliers | `[0.65, 0.65, 0.65]` | Default |

---

## 4. How Other Team Members Can Use This Module

### A. Member 2: Adaptive-Grid Mapping Engineer
In your mapping script, run inference directly:

```python
from src.ai.inference import SemanticSegmenter

# 1. Initialize segmenter (loads model checkpoint if available)
segmenter = SemanticSegmenter(model_path="checkpoints/best_randlanet.pt", num_points=4096)

# 2. Run inference on a LiDAR frame
result = segmenter.predict_file("data/sample_kitti/sequences/00/velodyne/000000.bin")

# 3. Access coordinates, labels, and confidence
points = result["points"]                   # (N, 4): x, y, z, intensity
labels = result["predicted_labels"]         # (N,): 0 to 7
confidences = result["confidence_scores"]   # (N,): probability

# 4. Filter dynamic or critical objects for variable-resolution grid allocation:
is_pedestrian = (labels == 5)
is_vehicle = (labels == 4)
critical_points = points[is_pedestrian | is_vehicle]
```

### B. Member 3: Visualization & Dashboard Engineer
To colorize points or convert predictions to PLY for 3D web/desktop rendering:

```python
from src.ai.label_mapping import colorize_mapped_labels
from src.visualization.pointcloud_viewer import PointCloudVisualizer

# Convert integer labels [0-7] directly into RGB colors (float32 [0-1] or uint8 [0-255])
rgb_colors = colorize_mapped_labels(result["predicted_labels"], as_float=True)

# Export standard PLY point cloud for 3D viewers (Three.js, Open3D, MeshLab)
PointCloudVisualizer.export_ply_raw(result["points"][:, :3], rgb_colors, "output_frame.ply")
```

---

## 5. Execution & CLI Commands

### Run Unit & Integration Tests
```powershell
python -m pytest -v tests/test_ai_data_pipeline.py
```

### Inspect a Real LiDAR `.bin` Frame
```powershell
python -m src.data.lidar_loader data/semantic_kitti/sequences/00/velodyne/000000.bin
```

### Inspect a Real Label `.label` File
```powershell
python -m src.data.label_loader data/semantic_kitti/sequences/00/labels/000000.label
```

### Run Inference on Real Scan using Trained Checkpoint
```powershell
python -m src.ai.inference data/semantic_kitti/sequences/00/velodyne/000000.bin --model-path checkpoints/best_randlanet_real.pt
```

### Train on Multi-Frame Dataset (Zero-Leakage Split: Seq 00)
```powershell
python -m src.ai.train --data-root data/sample_kitti --train-seq 00 --val-seq 00 --epochs 5 --batch-size 1 --points 2048
```
*(When additional authentic SemanticKITTI sequences are downloaded, pass `--data-root data/semantic_kitti --train-seq 00 --val-seq 01`)*

### Run 3-Way Visual Verification (Ground Truth vs Prediction vs Error Map)
```powershell
python -m src.visualization.pointcloud_viewer --bin data/semantic_kitti/sequences/00/velodyne/000000.bin --label data/semantic_kitti/sequences/00/labels/000000.label --checkpoint checkpoints/best_randlanet_real.pt
```

### Setup Open3D Environment (Python 3.11)
```powershell
.\scripts\setup_env.ps1
```

