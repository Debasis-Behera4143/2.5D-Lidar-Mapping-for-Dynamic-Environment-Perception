"""
SemanticKITTI to Project Taxonomy Label Mapping.

Defines the 8-class project taxonomy:
    0: road
    1: sidewalk
    2: building
    3: vegetation
    4: vehicle
    5: pedestrian
    6: pole_sign
    7: other

Provides an O(1) vectorized Lookup Table (LUT) mapping raw SemanticKITTI
IDs into the 8-class taxonomy, along with distinct RGB color palettes.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np


# Ordered list of project classes
PROJECT_CLASSES: List[str] = [
    "road",         # 0
    "sidewalk",     # 1
    "building",     # 2
    "vegetation",   # 3
    "vehicle",      # 4
    "pedestrian",   # 5
    "pole_sign",    # 6
    "other",        # 7
]

NUM_CLASSES: int = len(PROJECT_CLASSES)

CLASS_TO_ID: Dict[str, int] = {name: idx for idx, name in enumerate(PROJECT_CLASSES)}
ID_TO_CLASS: Dict[int, str] = {idx: name for idx, name in enumerate(PROJECT_CLASSES)}

# Ignored class index: class 7 ('other') contains unannotated points and laser outliers
IGNORE_LABEL_ID: int = 7
IGNORE_LABEL_NAME: str = "other"
# Standard 7 semantic evaluation classes (excluding noise/unlabeled 'other')
VALID_EVAL_CLASSES: List[int] = [0, 1, 2, 3, 4, 5, 6]

# SemanticKITTI raw IDs to project class names
RAW_TO_PROJECT_CLASS: Dict[int, str] = {
    # Unlabeled / Outlier
    0: "other",
    1: "other",
    # Vehicles (stationary)
    10: "vehicle",       # car
    11: "vehicle",       # bicycle
    13: "vehicle",       # bus
    15: "vehicle",       # motorcycle
    16: "vehicle",       # on-rails
    18: "vehicle",       # truck
    20: "vehicle",       # other-vehicle
    # Pedestrians / Humans
    30: "pedestrian",    # person
    31: "pedestrian",    # bicyclist
    32: "pedestrian",    # motorcyclist
    # Ground / Road
    40: "road",          # road
    44: "road",          # parking
    60: "road",          # lane-marking
    # Sidewalk / Ground
    48: "sidewalk",      # sidewalk
    49: "sidewalk",      # other-ground
    # Structures
    50: "building",      # building
    51: "building",      # fence
    52: "building",      # other-structure
    # Nature
    70: "vegetation",    # vegetation
    71: "vegetation",    # trunk
    72: "vegetation",    # terrain
    # Objects / Signs
    80: "pole_sign",     # pole
    81: "pole_sign",     # traffic-sign
    99: "pole_sign",     # other-object
    # Moving objects (raw + 250 in SemanticKITTI)
    252: "vehicle",      # moving car
    253: "pedestrian",   # moving bicyclist
    254: "pedestrian",   # moving person
    255: "pedestrian",   # moving motorcyclist
    256: "vehicle",      # moving on-rails
    257: "vehicle",      # moving bus
    258: "vehicle",      # moving truck
    259: "vehicle",      # moving other-vehicle
}

# Color palette normalized to [0.0, 1.0] for Open3D / matplotlib
CLASS_COLORS_FLOAT: Dict[int, Tuple[float, float, float]] = {
    0: (0.50, 0.25, 0.50),  # road: Purple
    1: (0.96, 0.14, 0.59),  # sidewalk: Pink
    2: (0.35, 0.35, 0.35),  # building: Dark Gray
    3: (0.22, 0.60, 0.22),  # vegetation: Green
    4: (0.20, 0.50, 0.90),  # vehicle: Blue
    5: (0.90, 0.15, 0.15),  # pedestrian: Red
    6: (1.00, 0.85, 0.10),  # pole_sign: Yellow
    7: (0.65, 0.65, 0.65),  # other: Light Gray
}

# Color palette in [0, 255] uint8
CLASS_COLORS_UINT8: Dict[int, Tuple[int, int, int]] = {
    cls_id: (int(r * 255), int(g * 255), int(b * 255))
    for cls_id, (r, g, b) in CLASS_COLORS_FLOAT.items()
}


def _build_lut(max_id: int = 65536) -> np.ndarray:
    """
    Build a 65536-element Look-Up Table array for O(1) label mapping.
    Any unmapped raw ID defaults to 'other' (class ID 7).
    """
    other_id = CLASS_TO_ID["other"]
    lut = np.full(max_id, other_id, dtype=np.int64)

    for raw_id, class_name in RAW_TO_PROJECT_CLASS.items():
        if raw_id < max_id:
            lut[raw_id] = CLASS_TO_ID[class_name]

    return lut


# Precomputed LUT for fast vectorized mapping
LABEL_LUT: np.ndarray = _build_lut()


def map_raw_to_project_labels(semantic_ids: np.ndarray) -> np.ndarray:
    """
    Map raw SemanticKITTI 16-bit IDs to project 8-class taxonomy (0-7).

    Args:
        semantic_ids: (N,) integer array of raw SemanticKITTI class IDs.

    Returns:
        np.ndarray: (N,) int64 array with mapped labels in [0, 7].
    """
    # Safe indexing into LUT
    clipped = np.clip(semantic_ids, 0, len(LABEL_LUT) - 1)
    return LABEL_LUT[clipped]


def colorize_mapped_labels(
    mapped_labels: np.ndarray,
    as_float: bool = True,
) -> np.ndarray:
    """
    Colorize mapped labels (0-7) into RGB point colors for Open3D rendering.

    Args:
        mapped_labels: (N,) integer array with values in [0, 7].
        as_float: If True, returns float32 in [0.0, 1.0], else uint8 in [0, 255].

    Returns:
        np.ndarray: (N, 3) color array.
    """
    if as_float:
        lut_colors = np.array([CLASS_COLORS_FLOAT[i] for i in range(NUM_CLASSES)], dtype=np.float32)
    else:
        lut_colors = np.array([CLASS_COLORS_UINT8[i] for i in range(NUM_CLASSES)], dtype=np.uint8)

    safe_labels = np.clip(mapped_labels, 0, NUM_CLASSES - 1)
    return lut_colors[safe_labels]


if __name__ == "__main__":
    print("Project Taxonomy (8 classes):")
    for idx, name in enumerate(PROJECT_CLASSES):
        color = CLASS_COLORS_FLOAT[idx]
        print(f"  Class {idx}: {name:<12} (RGB: {color})")

    # Quick test
    test_raw = np.array([40, 48, 50, 70, 10, 30, 80, 0, 252, 999], dtype=np.uint32)
    mapped = map_raw_to_project_labels(test_raw)
    for raw, m in zip(test_raw, mapped):
        print(f"Raw {raw:>3d} -> Mapped {m} ({ID_TO_CLASS[m]})")
