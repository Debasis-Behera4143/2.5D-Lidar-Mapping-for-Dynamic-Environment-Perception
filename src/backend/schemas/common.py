"""
Common data schemas and base models for backend API responses.

Includes standard success/error envelopes, spatial bounds, and reusable validators
for coordinate bounding boxes, paths, confidences, and percentages.
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, Sequence, Tuple, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

DataT = TypeVar("DataT")


def current_utc_iso() -> str:
    """Return current UTC time formatted as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def validate_non_empty_str(v: str, field_name: str = "field") -> str:
    """Ensure a string is non-empty and not just whitespace."""
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return v.strip()


class ErrorDetail(BaseModel):
    """Granular error information detailing field-level or contextual issues."""

    code: str = Field(description="Machine-readable error code, e.g. INVALID_BOUNDS")
    message: str = Field(description="Human-readable error description")
    location: Optional[str] = Field(
        default=None,
        description="Path, parameter, or field name where the error occurred",
    )

    model_config = ConfigDict(extra="forbid")


class BaseResponse(BaseModel):
    """Base API response envelope."""

    success: bool = Field(default=True, description="True if operation succeeded, False otherwise")
    message: str = Field(default="Operation completed successfully", description="Status message")
    timestamp: str = Field(
        default_factory=current_utc_iso,
        description="UTC timestamp of response generation in ISO 8601 format",
    )

    model_config = ConfigDict(extra="forbid")


class SuccessResponse(BaseResponse, Generic[DataT]):
    """Standard success response envelope wrapping optional typed payload."""

    success: bool = Field(default=True, description="Always True for success responses")
    data: Optional[DataT] = Field(default=None, description="Response payload data")


class ErrorResponse(BaseResponse):
    """Standard error response envelope."""

    success: bool = Field(default=False, description="Always False for error responses")
    message: str = Field(default="An error occurred", description="General error summary")
    error: str = Field(description="Primary error explanation")
    details: List[ErrorDetail] = Field(
        default_factory=list,
        description="Optional list of specific error details",
    )


class SpatialBounds(BaseModel):
    """
    3D spatial bounding box: [min_x, max_x, min_y, max_y, min_z, max_z].

    Enforces that minimum coordinates are strictly less than maximum coordinates.
    """

    min_x: float = Field(description="Minimum X coordinate in meters")
    max_x: float = Field(description="Maximum X coordinate in meters")
    min_y: float = Field(description="Minimum Y coordinate in meters")
    max_y: float = Field(description="Maximum Y coordinate in meters")
    min_z: float = Field(description="Minimum Z coordinate in meters")
    max_z: float = Field(description="Maximum Z coordinate in meters")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_spatial_bounds(self) -> "SpatialBounds":
        """Validate that minimum bounds are strictly less than maximum bounds."""
        if self.min_x >= self.max_x:
            raise ValueError(f"min_x ({self.min_x}) must be strictly less than max_x ({self.max_x})")
        if self.min_y >= self.max_y:
            raise ValueError(f"min_y ({self.min_y}) must be strictly less than max_y ({self.max_y})")
        if self.min_z >= self.max_z:
            raise ValueError(f"min_z ({self.min_z}) must be strictly less than max_z ({self.max_z})")
        return self

    def to_tuple(self) -> Tuple[float, float, float, float, float, float]:
        """Convert bounds to a standard 6-tuple."""
        return (self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z)

    @classmethod
    def from_tuple(cls, bounds: Sequence[float]) -> "SpatialBounds":
        """Instantiate SpatialBounds from a sequence of 6 floats."""
        if len(bounds) != 6:
            raise ValueError(f"Expected 6 bounds elements, got {len(bounds)}")
        return cls(
            min_x=float(bounds[0]),
            max_x=float(bounds[1]),
            min_y=float(bounds[2]),
            max_y=float(bounds[3]),
            min_z=float(bounds[4]),
            max_z=float(bounds[5]),
        )


class ROIBounds(SpatialBounds):
    """
    Region of Interest (ROI) bounding box.

    Supports initialization from a dictionary or a 6-element tuple/list of floats:
    (min_x, max_x, min_y, max_y, min_z, max_z).
    """

    @model_validator(mode="before")
    @classmethod
    def parse_sequence_or_dict(cls, data: Any) -> Any:
        if isinstance(data, (list, tuple)):
            if len(data) != 6:
                raise ValueError(
                    f"ROI bounds sequence must contain exactly 6 elements: (min_x, max_x, min_y, max_y, min_z, max_z), got {len(data)}"
                )
            return {
                "min_x": float(data[0]),
                "max_x": float(data[1]),
                "min_y": float(data[2]),
                "max_y": float(data[3]),
                "min_z": float(data[4]),
                "max_z": float(data[5]),
            }
        return data
