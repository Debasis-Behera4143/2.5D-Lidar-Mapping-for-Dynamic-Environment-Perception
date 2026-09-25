"""
LiDAR Semantic Segmentation inference schemas.

Defines request and response contracts for point cloud perception,
including downsampling parameters, confidence statistics, class distributions,
spatial bounds, and preview points.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.backend.schemas.common import BaseResponse, SpatialBounds, validate_non_empty_str


class InferenceRequest(BaseModel):
    """Input payload for point cloud semantic segmentation inference."""

    bin_path: str = Field(
        min_length=1,
        description="Path to the binary LiDAR scan (.bin file)",
    )
    label_path: Optional[str] = Field(
        default=None,
        description="Optional path to ground truth label (.label file) for evaluation",
    )
    num_points: Optional[int] = Field(
        default=None,
        description="Optional target number of points for model downsampling; leave unset to keep the full frame intact.",
    )
    interpolate_to_full: bool = Field(
        default=False,
        description="If True, interpolates sampled predictions back to the dense point cloud",
    )
    preview_points_limit: int = Field(
        default=2000,
        gt=0,
        description="Maximum number of points returned in the response preview (> 0)",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("bin_path")
    @classmethod
    def validate_bin_path(cls, v: str) -> str:
        return validate_non_empty_str(v, "bin_path")

    @field_validator("label_path")
    @classmethod
    def validate_label_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_non_empty_str(v, "label_path")
        return v

    @field_validator("num_points")
    @classmethod
    def validate_num_points(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("num_points must be strictly positive (> 0) if provided")
        return v


class ConfidenceSummary(BaseModel):
    """Statistical summary of prediction confidence scores in range [0.0, 1.0]."""

    mean: float = Field(
        ge=0.0,
        le=1.0,
        description="Mean softmax confidence score across points [0.0, 1.0]",
    )
    min: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum confidence score [0.0, 1.0]",
    )
    max: float = Field(
        ge=0.0,
        le=1.0,
        description="Maximum confidence score [0.0, 1.0]",
    )
    std: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Standard deviation of confidence scores",
    )

    model_config = ConfigDict(extra="forbid")


class PointPreviewItem(BaseModel):
    """Individual 3D point record for visualization preview."""

    x: float = Field(description="Forward coordinate in meters")
    y: float = Field(description="Lateral coordinate in meters")
    z: float = Field(description="Vertical height in meters")
    intensity: float = Field(description="Reflectance / intensity measurement")
    predicted_label: int = Field(
        ge=0,
        le=7,
        description="Predicted semantic class ID (0 to 7)",
    )
    class_name: str = Field(description="Predicted class name")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Softmax prediction confidence in range [0.0, 1.0]",
    )
    ground_truth_label: Optional[int] = Field(
        default=None,
        ge=0,
        le=7,
        description="Ground truth class ID if available (0 to 7)",
    )

    model_config = ConfigDict(extra="forbid")


class InferenceEvaluationInfo(BaseModel):
    """Ground truth segmentation evaluation metrics."""

    accuracy_percent: float = Field(
        ge=0.0,
        le=100.0,
        description="Overall classification accuracy percentage [0.0, 100.0]",
    )
    mean_iou_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Mean Intersection-over-Union percentage [0.0, 100.0]",
    )
    evaluated_points: int = Field(
        gt=0,
        description="Total number of evaluated points (> 0)",
    )
    per_class_iou: Optional[Dict[str, float]] = Field(
        default=None,
        description="Per-class IoU percentages or ratios",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("per_class_iou")
    @classmethod
    def validate_per_class_iou(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            for k, val in v.items():
                if not (0.0 <= val <= 100.0):
                    raise ValueError(f"Per-class IoU for '{k}' must be between 0.0 and 100.0, got {val}")
        return v


class InferenceResponse(BaseResponse):
    """Output payload for LiDAR semantic segmentation inference."""

    frame_id: str = Field(description="LiDAR scan frame identifier, e.g. '000000'")
    total_points: int = Field(gt=0, description="Total number of points processed (> 0)")
    original_point_count: int = Field(gt=0, description="Original full-frame point count before any visualization downsampling")
    predicted_labels: List[int] = Field(
        description="Predicted class IDs for points (or downsampled points)",
    )
    confidence_information: ConfidenceSummary = Field(
        description="Confidence statistical metrics",
    )
    class_distribution: Dict[str, int] = Field(
        description="Point counts per predicted semantic class",
    )
    spatial_bounds: SpatialBounds = Field(
        description="Coordinate spatial bounding box of the points",
    )
    preview_points: List[PointPreviewItem] = Field(
        default_factory=list,
        description="Downsampled points for UI/visualizer rendering",
    )
    evaluation_information: Optional[InferenceEvaluationInfo] = Field(
        default=None,
        description="Evaluation results if ground-truth labels were provided",
    )

    @field_validator("predicted_labels")
    @classmethod
    def validate_predicted_labels(cls, v: List[int]) -> List[int]:
        for lbl in v:
            if not (0 <= lbl <= 7):
                raise ValueError(f"Predicted class ID {lbl} is invalid; must be between 0 and 7")
        return v
