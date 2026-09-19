"""
Configuration dataclasses for 2.5D uniform and adaptive LiDAR mapping.

Provides parameter objects with sensible defaults for grid cell resolutions,
region of interest clipping, heuristic importance weights, and movement thresholds.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class UniformGridConfig:
    """Configuration for uniform 2.5D grid mapping."""
    resolution: float = 0.50  # Cell size in meters (> 0)
    origin_x: float = 0.0     # Coordinate origin X offset
    origin_y: float = 0.0     # Coordinate origin Y offset
    # Optional ROI bounding box: (min_x, max_x, min_y, max_y, [min_z, max_z])
    roi_bounds: Optional[Tuple[float, ...]] = None

    def __post_init__(self):
        if self.resolution <= 0:
            raise ValueError(f"Resolution must be strictly positive (> 0), got {self.resolution}")


@dataclass
class ImportanceConfig:
    """
    Configuration weights for heuristic importance calculation.

    Scores are computed via a weighted linear combination normalized to [0, 1].
    NOTE: These are heuristic prototype scores, not learned importance values.
    """
    semantic_weight: float = 0.40
    uncertainty_weight: float = 0.20
    density_weight: float = 0.15
    height_weight: float = 0.15
    proximity_weight: float = 0.10

    # Default semantic priority scores per class (0-7)
    # High: pedestrian (5), vehicle (4)
    # Medium-High: pole_sign (6)
    # Medium: building (2), sidewalk (1), vegetation (3)
    # Low: road (0), other (7)
    semantic_scores: Dict[int, float] = field(default_factory=lambda: {
        0: 0.20,  # road: low
        1: 0.50,  # sidewalk: medium
        2: 0.50,  # building: medium
        3: 0.40,  # vegetation: medium
        4: 0.90,  # vehicle: high
        5: 1.00,  # pedestrian: high (ultra-critical)
        6: 0.70,  # pole_sign: medium-high
        7: 0.10,  # other: low
    })

    # Normalization scaling references
    max_density_ref: int = 40
    max_height_var_ref: float = 1.5
    max_proximity_ref: float = 40.0


@dataclass
class MovementConfig:
    """Configuration for frame-to-frame geometric movement estimation."""
    threshold: float = 0.25         # Displacement distance threshold in meters for moving points
    max_search_radius: float = 3.0  # Max KDTree radius query in meters


@dataclass
class AdaptiveConfig:
    """Configuration for adaptive coarse-to-fine 2.5D grid mapping."""
    base_resolution: float = 1.00       # Coarse base cell resolution in meters (> 0)
    fine_resolution: float = 0.25       # Fine subdivided cell resolution in meters (> 0)
    importance_threshold: float = 0.50  # Cell importance threshold to trigger subdivision [0, 1]
    dynamic_threshold: float = 0.25     # Movement ratio/displacement to trigger subdivision
    min_points_per_cell: int = 1        # Minimum points required to allocate a cell
    origin_x: float = 0.0               # Origin X offset
    origin_y: float = 0.0               # Origin Y offset
    roi_bounds: Optional[Tuple[float, ...]] = None

    def __post_init__(self):
        if self.base_resolution <= 0:
            raise ValueError(f"base_resolution must be strictly positive, got {self.base_resolution}")
        if self.fine_resolution <= 0:
            raise ValueError(f"fine_resolution must be strictly positive, got {self.fine_resolution}")
        if self.fine_resolution >= self.base_resolution:
            raise ValueError(
                f"fine_resolution ({self.fine_resolution}) must be smaller than base_resolution ({self.base_resolution})"
            )
        if not (0.0 <= self.importance_threshold <= 1.0):
            raise ValueError(f"importance_threshold must be in [0, 1], got {self.importance_threshold}")


@dataclass
class PipelineConfig:
    """Unified configuration container for end-to-end mapping pipeline execution."""
    uniform: UniformGridConfig = field(default_factory=UniformGridConfig)
    adaptive: AdaptiveConfig = field(default_factory=AdaptiveConfig)
    importance: ImportanceConfig = field(default_factory=ImportanceConfig)
    movement: MovementConfig = field(default_factory=MovementConfig)
