"""
Adaptive Variable-Resolution 2.5D LiDAR Mapping module.

Provides uniform grid mapping, coarse-to-fine adaptive grid allocation,
heuristic importance calculation, nearest-neighbor movement estimation,
and map comparison benchmarks.
"""

from src.mapping.adaptive_mapper import AdaptiveGridMapper
from src.mapping.cell_aggregator import CellAggregator
from src.mapping.config import (
    AdaptiveConfig,
    ImportanceConfig,
    MovementConfig,
    PipelineConfig,
    UniformGridConfig,
)
from src.mapping.grid_mapper import UniformGridMapper
from src.mapping.importance import (
    calculate_cell_importance,
    calculate_point_importance,
)
from src.mapping.metrics import compare_maps, compute_map_summary
from src.mapping.movement import estimate_movement
from src.mapping.pipeline import (
    generate_adaptive_map,
    generate_uniform_map,
    process_frame,
)
from src.mapping.serialization import to_json_serializable, to_json_string
from src.mapping.types import (
    NUM_CLASSES,
    PROJECT_CLASSES,
    MappingValidationError,
    ValidatedInput,
    validate_input_payload,
)

__all__ = [
    # Mappers
    "UniformGridMapper",
    "AdaptiveGridMapper",
    "CellAggregator",
    # Configs
    "UniformGridConfig",
    "AdaptiveConfig",
    "ImportanceConfig",
    "MovementConfig",
    "PipelineConfig",
    # Functions
    "calculate_point_importance",
    "calculate_cell_importance",
    "estimate_movement",
    "compute_map_summary",
    "compare_maps",
    "generate_uniform_map",
    "generate_adaptive_map",
    "process_frame",
    # Validation & Serialization
    "validate_input_payload",
    "MappingValidationError",
    "ValidatedInput",
    "to_json_serializable",
    "to_json_string",
    "PROJECT_CLASSES",
    "NUM_CLASSES",
]
