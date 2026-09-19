# Member 2 Handoff Guide: Adaptive-Grid Mapping Integration

**Role Hand-Off:** From Member 1 (AI/ML & LiDAR Data Engineering) to Member 2 (Adaptive-Grid Mapping Engineer)  
**Project:** Adaptive Variable-Resolution 2.5D LiDAR Mapping for Dynamic Environment Perception  
**Perception Engine:** RandLA-Net Semantic Segmentation + Standard Perception Output Contract  

---

## 1. Executive Summary & Integration Interface

Member 1 provides the perception layer that ingests raw LiDAR point clouds (Velodyne HDL-64E `.bin` files) and produces semantic class IDs and confidence probabilities.

Member 2 consumes this standardized output to allocate **variable resolution cells** in the 2.5D elevation and multi-layer occupancy grid (e.g., allocating fine $0.05\,\text{m}$ cells for pedestrians and $0.10\,\text{m}$ for vehicles, while using coarse $0.40-0.50\,\text{m}$ cells for road and distant buildings).

---

## 2. Quickstart Code Snippet for Member 2

In your mapping module (e.g. `src/mapping/grid_mapper.py`), initialize the perception engine and run inference:

```python
from pathlib import Path
import numpy as np
from src.ai.inference import SemanticSegmenter
from src.ai.label_mapping import CLASS_TO_ID, PROJECT_CLASSES

# 1. Initialize SemanticSegmenter (auto-detects CUDA/CPU)
segmenter = SemanticSegmenter(
    model_path="checkpoints/best_randlanet_real.pt",
    num_points=4096,   # Target points for network downsampling
    k_neighbors=12,
)

# 2. Run inference on a LiDAR scan
# Set interpolate_to_full=True to receive labels for the entire dense scan (~120k points)
# Set interpolate_to_full=False to receive downsampled points (e.g., 4096 points for fast testing)
result = segmenter.predict_file(
    bin_path="data/semantic_kitti/sequences/00/velodyne/000000.bin",
    interpolate_to_full=True,
)

# 3. Access standard perception fields
points = result["points"]                   # np.ndarray, shape (N, 4): [X, Y, Z, Intensity]
labels = result["predicted_labels"]         # np.ndarray, shape (N,): Class IDs in [0, 7]
confidences = result["confidence_scores"]   # np.ndarray, shape (N,): Softmax probability [0.0, 1.0]
frame_id = result["frame_id"]               # str: e.g. "000000"

# 4. Filter critical dynamic/vulnerable objects for variable-resolution grid allocation
pedestrian_mask = (labels == CLASS_TO_ID["pedestrian"])
vehicle_mask = (labels == CLASS_TO_ID["vehicle"])
ground_mask = (labels == CLASS_TO_ID["road"]) | (labels == CLASS_TO_ID["sidewalk"])

pedestrian_points = points[pedestrian_mask]  # Target for ultra-fine grid (0.05m)
vehicle_points = points[vehicle_mask]        # Target for fine grid (0.10m)
ground_points = points[ground_mask]          # Target for coarse/elevation surface (0.40m)
```

---

## 3. Standard Output Contract Schema

Every perception call strictly complies with the following dictionary structure:

```python
{
    "points": np.ndarray,            # Shape: (N, 4), dtype: float32 -> [X, Y, Z, Intensity]
    "predicted_labels": np.ndarray,  # Shape: (N,), dtype: int64   -> Class ID in [0, 7]
    "confidence_scores": np.ndarray, # Shape: (N,), dtype: float32 -> Softmax probability [0.0, 1.0]
    "frame_id": str                  # e.g., "000000"
}
```

### Coordinate System & Units
- **$X$ (meters):** Forward direction along the vehicle heading.
- **$Y$ (meters):** Left lateral direction.
- **$Z$ (meters):** Vertical height above the LiDAR sensor.
- **Intensity:** Sensor remission value in range $[0.0, 1.0]$.
- **Sensor:** Velodyne HDL-64E mounted on vehicle roof ($\approx 1.73\,\text{m}$ ground clearance).

---

## 4. 8-Class Project Taxonomy & Resolution Allocation

The project unifies raw SemanticKITTI classes into 8 distinct functional classes:

| Class ID | Class Name | Included Raw Semantic Classes | Perception Priority | Recommended Grid Cell Resolution |
|---|---|---|---|---|
| **0** | `road` | Road surface, parking, lane markings | Ground Base | **Coarse / Medium ($0.40\,\text{m}$)** |
| **1** | `sidewalk` | Sidewalk, ground curbs | Boundary | **Medium ($0.20\,\text{m}$)** |
| **2** | `building` | Buildings, fences, walls | Static Barrier | **Coarse ($0.50\,\text{m}$)** |
| **3** | `vegetation` | Trees, bushes, foliage, terrain | Soft Obstacle | **Medium ($0.30\,\text{m}$)** |
| **4** | `vehicle` | Cars, trucks, buses, motorcycles | **Dynamic Critical** | **Fine ($0.10\,\text{m}$)** |
| **5** | `pedestrian` | Pedestrians, bicyclists | **Ultra-Critical** | **Ultra-Fine ($0.05\,\text{m}$)** |
| **6** | `pole_sign` | Poles, traffic signs, traffic lights | Vertical Obstacle | **Fine ($0.10\,\text{m}$)** |
| **7** | `other` | Outliers, unlabeled, background | Noise / Default | **Default ($0.40\,\text{m}$)** |

---

## 5. Important Note Regarding Baseline Model Performance

> [!WARNING]
> **Honest Engineering Status:**  
> The current PyTorch checkpoint (`checkpoints/best_randlanet_real.pt`) is an **early baseline prototype** trained on CPU for 1 epoch. Its current classification accuracy is $\approx 2.5\%$, and mIoU is $\approx 5.7\%$. Predictions are noisy.
>
> **Recommended Strategy for Member 2:**
> 1. **To test your adaptive grid allocation algorithm:** You can pass authentic ground-truth labels directly to verify that fine resolution cells trigger for vehicles/pedestrians:
>    ```python
>    from src.data.label_loader import LabelLoader
>    from src.ai.label_mapping import map_raw_to_project_labels
>    
>    _, raw_sem, _ = LabelLoader.load_label("data/semantic_kitti/sequences/00/labels/000000.label")
>    gt_labels = map_raw_to_project_labels(raw_sem)
>    # Use gt_labels to validate adaptive grid mechanics with 100% ground truth confidence!
>    ```
> 2. **To test end-to-end integration:** Use `segmenter.predict_file(...)`. The interface and contracts are 100% final and will not change when more mature model checkpoints are loaded.

---

## 6. Full-Cloud vs Downsampled Inference Modes

| Parameter | `interpolate_to_full=False` (Default) | `interpolate_to_full=True` |
|---|---|---|
| **Point Count** | Subsampled $N \approx 4,096$ points | Full clean scan $N \approx 120,000$ points |
| **Interpolation** | None (direct network output) | Fast 1-NN KDTree interpolation ($O(N \log M)$) |
| **Latency** | Extremely fast ($\approx 25\,\text{ms}$) | Fast ($\approx 65\,\text{ms}$) |
| **Use Case** | Real-time tracking, fast tests | Dense 2.5D elevation grid generation |
