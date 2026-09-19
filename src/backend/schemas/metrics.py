"""
Model performance and benchmark metrics schemas.

Tracks latency, throughput, overall accuracy, mIoU, and includes honest engineering
status disclosures regarding baseline prototypes.
"""

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.backend.schemas.common import BaseResponse


class MetricsResponse(BaseResponse):
    """Performance benchmarks and operational metrics for perception and mapping."""

    model_name: str = Field(
        default="RandLA-Net",
        description="Name of the semantic segmentation architecture",
    )
    device: str = Field(
        description="Execution compute device ('cpu' or 'cuda')",
    )
    number_of_classes: int = Field(
        default=8,
        gt=0,
        description="Number of target semantic classes",
    )
    inference_latency: float = Field(
        ge=0.0,
        description="Average inference latency in seconds per scan (>= 0.0)",
    )
    throughput: float = Field(
        ge=0.0,
        description="Processing throughput in points per second (>= 0.0)",
    )
    accuracy: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall classification accuracy percentage in range [0.0, 100.0]",
    )
    mIoU: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Mean Intersection over Union percentage in range [0.0, 100.0]",
    )
    prototype_status: str = Field(
        default="baseline_prototype_1_epoch",
        description="Current prototype training maturity status",
    )
    limitation_note: str = Field(
        default=(
            "The current checkpoint is an early baseline prototype trained on CPU for 1 epoch. "
            "Predictions are noisy (accuracy ~2.5%, mIoU ~5.7%). Ground-truth labels should be used "
            "to validate variable-resolution grid allocation mechanics with high confidence."
        ),
        description="Engineering disclosure of model baseline status and performance bounds",
    )
    per_class_iou: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional breakdown of IoU percentages per class name",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("per_class_iou")
    @classmethod
    def validate_per_class_iou(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if v is not None:
            for cls_name, iou in v.items():
                if not (0.0 <= iou <= 100.0):
                    raise ValueError(f"IoU for class '{cls_name}' must be between 0.0 and 100.0, got {iou}")
        return v
