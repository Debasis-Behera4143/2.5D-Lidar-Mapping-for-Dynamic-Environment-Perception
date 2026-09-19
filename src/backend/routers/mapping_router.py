"""
FastAPI route endpoints for 2.5D uniform and adaptive LiDAR mapping.

Provides REST endpoints:
- POST /api/v1/map/uniform
- POST /api/v1/map/adaptive
- POST /api/v1/map/compare
"""

from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.backend.services.mapping_service import MappingService
from src.mapping.types import MappingValidationError

router = APIRouter(prefix="/api/v1/map", tags=["Mapping"])
service = MappingService()


class UniformMapRequest(BaseModel):
    """Payload for generating a uniform 2.5D grid map."""
    perception: Dict[str, Any] = Field(
        description="Perception output dictionary containing points, predicted_labels, confidence_scores, frame_id"
    )
    resolution: float = Field(default=0.50, gt=0.0, description="Grid cell resolution in meters (> 0)")
    roi_bounds: Optional[Tuple[float, ...]] = Field(default=None, description="Optional ROI bounding box")


class AdaptiveMapRequest(BaseModel):
    """Payload for generating an adaptive variable-resolution 2.5D grid map."""
    perception: Dict[str, Any] = Field(
        description="Current frame perception output dictionary"
    )
    previous_perception: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional previous frame perception output for movement estimation"
    )
    base_resolution: float = Field(default=1.00, gt=0.0, description="Coarse base resolution in meters")
    fine_resolution: float = Field(default=0.25, gt=0.0, description="Fine resolution in meters")
    importance_threshold: float = Field(default=0.50, ge=0.0, le=1.0, description="Importance cutoff")
    dynamic_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="Movement threshold")
    roi_bounds: Optional[Tuple[float, ...]] = Field(default=None, description="Optional ROI bounding box")


class CompareMapsRequest(BaseModel):
    """Payload for comparing uniform and adaptive maps."""
    uniform_map: Dict[str, Any] = Field(description="Uniform map dictionary")
    adaptive_map: Dict[str, Any] = Field(description="Adaptive map dictionary")


@router.post("/uniform", status_code=status.HTTP_200_OK)
def create_uniform_map(req: UniformMapRequest) -> Dict[str, Any]:
    """Generate a uniform 2.5D grid map from perception input."""
    try:
        return service.generate_uniform_map(
            payload=req.perception,
            resolution=req.resolution,
            roi_bounds=req.roi_bounds,
        )
    except (MappingValidationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Mapping failed: {e}")


@router.post("/adaptive", status_code=status.HTTP_200_OK)
def create_adaptive_map(req: AdaptiveMapRequest) -> Dict[str, Any]:
    """Generate an adaptive variable-resolution 2.5D grid map from perception input."""
    try:
        return service.generate_adaptive_map(
            payload=req.perception,
            previous_payload=req.previous_perception,
            base_resolution=req.base_resolution,
            fine_resolution=req.fine_resolution,
            importance_threshold=req.importance_threshold,
            dynamic_threshold=req.dynamic_threshold,
            roi_bounds=req.roi_bounds,
        )
    except (MappingValidationError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Adaptive mapping failed: {e}")


@router.post("/compare", status_code=status.HTTP_200_OK)
def compare_uniform_adaptive_maps(req: CompareMapsRequest) -> Dict[str, Any]:
    """Compare uniform and adaptive maps and return efficiency benchmarks."""
    try:
        return service.compare_maps(req.uniform_map, req.adaptive_map)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Comparison failed: {e}")
