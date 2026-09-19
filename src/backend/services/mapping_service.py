"""
Mapping Service Adapter for Member 2 Backend integration.

Bridges perception inference results (from Member 1 or Member 2 schemas)
with the Member 3 2.5D uniform and adaptive LiDAR mapping pipeline.
"""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np

from src.mapping.config import (
    AdaptiveConfig,
    ImportanceConfig,
    MovementConfig,
    PipelineConfig,
    UniformGridConfig,
)
from src.mapping.pipeline import (
    compare_maps as pipeline_compare_maps,
    generate_adaptive_map as pipeline_generate_adaptive_map,
    generate_uniform_map as pipeline_generate_uniform_map,
    process_frame as pipeline_process_frame,
)
from src.mapping.serialization import to_json_serializable


class MappingService:
    """
    Service adapter exposing high-level uniform and adaptive mapping operations
    to backend routers or standalone CLI/batch scripts.
    """

    @staticmethod
    def _normalize_payload(payload: Any) -> Dict[str, Any]:
        """Convert Pydantic models or objects into standard perception dictionary."""
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        elif isinstance(payload, dict):
            return payload
        raise TypeError(f"Unsupported perception payload type: {type(payload).__name__}")

    def generate_uniform_map(
        self,
        payload: Any,
        resolution: float = 0.50,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a uniform 2.5D grid map.

        Args:
            payload: Perception result dictionary or InferenceResponse model.
            resolution: Cell resolution in meters.
            roi_bounds: Optional ROI bounding box tuple.

        Returns:
            JSON-serializable uniform grid map dictionary.
        """
        norm_payload = self._normalize_payload(payload)
        cfg = UniformGridConfig(resolution=resolution, roi_bounds=roi_bounds)
        return pipeline_generate_uniform_map(norm_payload, config=cfg)

    def generate_adaptive_map(
        self,
        payload: Any,
        previous_payload: Optional[Any] = None,
        base_resolution: float = 1.00,
        fine_resolution: float = 0.25,
        importance_threshold: float = 0.50,
        dynamic_threshold: float = 0.25,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an adaptive variable-resolution 2.5D grid map.

        Args:
            payload: Current frame perception payload.
            previous_payload: Optional preceding frame perception payload.
            base_resolution: Coarse base cell resolution in meters.
            fine_resolution: Fine cell resolution in meters.
            importance_threshold: Heuristic cutoff to trigger cell subdivision.
            dynamic_threshold: Movement threshold for dynamic marking.
            roi_bounds: Optional ROI bounding box tuple.

        Returns:
            JSON-serializable adaptive grid map dictionary.
        """
        norm_curr = self._normalize_payload(payload)
        norm_prev = self._normalize_payload(previous_payload) if previous_payload is not None else None

        ada_cfg = AdaptiveConfig(
            base_resolution=base_resolution,
            fine_resolution=fine_resolution,
            importance_threshold=importance_threshold,
            dynamic_threshold=dynamic_threshold,
            roi_bounds=roi_bounds,
        )
        return pipeline_generate_adaptive_map(norm_curr, previous_payload=norm_prev, config=ada_cfg)

    def compare_maps(
        self,
        uniform_map: Dict[str, Any],
        adaptive_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare uniform and adaptive maps and return efficiency metrics.

        Args:
            uniform_map: Uniform map output dictionary.
            adaptive_map: Adaptive map output dictionary.

        Returns:
            JSON-serializable comparison dictionary.
        """
        return pipeline_compare_maps(uniform_map, adaptive_map)

    def process_frame(
        self,
        payload: Any,
        previous_payload: Optional[Any] = None,
        pipeline_config: Optional[PipelineConfig] = None,
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end mapping pipeline on a frame.

        Args:
            payload: Current frame perception payload.
            previous_payload: Optional previous frame perception payload.
            pipeline_config: Optional PipelineConfig.

        Returns:
            Comprehensive JSON-serializable mapping dictionary.
        """
        norm_curr = self._normalize_payload(payload)
        norm_prev = self._normalize_payload(previous_payload) if previous_payload is not None else None
        return pipeline_process_frame(norm_curr, previous_payload=norm_prev, config=pipeline_config)
