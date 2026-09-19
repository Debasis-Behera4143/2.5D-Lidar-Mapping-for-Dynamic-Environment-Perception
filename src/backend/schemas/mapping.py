"""
Adaptive variable-resolution 2.5D grid mapping schemas.

Defines request and response contracts for multi-layer elevation and occupancy
mapping with dynamic cell resolution allocation based on semantic class priority.
"""

from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from src.backend.schemas.common import BaseResponse, ROIBounds, SpatialBounds, validate_non_empty_str


class MappingRequest(BaseModel):
    """Input payload for generating an adaptive variable-resolution 2.5D grid map."""

    bin_path: str = Field(
        min_length=1,
        description="Path to the binary LiDAR scan (.bin file)",
    )
    roi_bounds: ROIBounds = Field(
        default_factory=lambda: ROIBounds(
            min_x=-40.0, max_x=40.0,
            min_y=-40.0, max_y=40.0,
            min_z=-3.0, max_z=4.0,
        ),
        description="Region of Interest bounding box (min_x, max_x, min_y, max_y, min_z, max_z)",
    )
    interpolate_to_full: bool = Field(
        default=True,
        description="Whether to interpolate predictions to the dense scan before mapping",
    )
    coarse_resolution: float = Field(
        default=0.40,
        gt=0.0,
        description="Coarse resolution cell size in meters for static ground/buildings (> 0)",
    )
    fine_resolution: float = Field(
        default=0.10,
        gt=0.0,
        description="Fine resolution cell size in meters for vehicles/poles (> 0)",
    )
    pedestrian_resolution: float = Field(
        default=0.05,
        gt=0.0,
        description="Ultra-fine resolution cell size in meters for vulnerable road users (> 0)",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("bin_path")
    @classmethod
    def validate_bin_path(cls, v: str) -> str:
        return validate_non_empty_str(v, "bin_path")

    @model_validator(mode="after")
    def validate_resolutions(self) -> "MappingRequest":
        """Ensure positive resolution values."""
        if self.pedestrian_resolution <= 0 or self.fine_resolution <= 0 or self.coarse_resolution <= 0:
            raise ValueError("All grid cell resolutions must be strictly positive (> 0)")
        return self


class MemoryEstimate(BaseModel):
    """Memory usage breakdown for the allocated multi-resolution grid structure."""

    estimated_bytes: int = Field(
        ge=0,
        description="Estimated memory consumption in bytes",
    )
    estimated_mb: float = Field(
        ge=0.0,
        description="Estimated memory consumption in megabytes",
    )
    formatted: str = Field(
        description="Human-readable memory string (e.g. '14.2 MB')",
    )

    model_config = ConfigDict(extra="forbid")


class GridCellPreview(BaseModel):
    """Representative grid cell for map visualization."""

    center_x: float = Field(description="Cell center X position in meters")
    center_y: float = Field(description="Cell center Y position in meters")
    resolution: float = Field(
        gt=0.0,
        description="Grid cell edge length in meters (> 0)",
    )
    elevation_min: float = Field(description="Minimum surface elevation in meters")
    elevation_max: float = Field(description="Maximum surface elevation in meters")
    dominant_class_id: int = Field(
        ge=0,
        le=7,
        description="Dominant semantic class ID (0 to 7)",
    )
    dominant_class_name: str = Field(description="Dominant semantic class name")
    point_count: int = Field(
        ge=0,
        description="Number of points mapped into this cell",
    )
    occupancy: float = Field(
        ge=0.0,
        le=1.0,
        description="Occupancy probability score in range [0.0, 1.0]",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_elevation(self) -> "GridCellPreview":
        if self.elevation_min > self.elevation_max:
            raise ValueError(
                f"elevation_min ({self.elevation_min}) cannot exceed elevation_max ({self.elevation_max})"
            )
        return self


class MappingResponse(BaseResponse):
    """Output payload representing the generated adaptive variable-resolution 2.5D map."""

    frame_id: str = Field(description="LiDAR frame identifier, e.g. '000000'")
    status: str = Field(
        default="completed",
        description="Processing status e.g. 'completed', 'success'",
    )
    grid_type: str = Field(
        default="adaptive_variable_resolution_2.5d",
        description="Grid architecture type identifier",
    )
    execution_time: float = Field(
        ge=0.0,
        description="Processing time in seconds (>= 0.0)",
    )
    total_input_points: int = Field(
        ge=0,
        description="Total LiDAR input points ingested",
    )
    allocated_cells: int = Field(
        ge=0,
        description="Total multi-resolution cells allocated",
    )
    memory_estimate: MemoryEstimate = Field(
        description="Estimated memory consumption",
    )
    resolution_breakdown: Dict[str, int] = Field(
        description="Count of allocated cells per resolution tier",
    )
    map_bounds: SpatialBounds = Field(
        description="Actual spatial bounds occupied by the map",
    )
    preview_grid_cells: List[GridCellPreview] = Field(
        default_factory=list,
        description="Sample of grid cells for map visualization",
    )
