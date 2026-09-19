"""
Dataset sample discovery and LiDAR file inspection schemas.

Provides schemas for point cloud files, frame sequences, file sizes,
and label availability in the dataset directory structure.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.backend.schemas.common import BaseResponse, validate_non_empty_str


class SampleItem(BaseModel):
    """Metadata describing a LiDAR scan sample frame."""

    dataset_type: str = Field(
        min_length=1,
        description="Dataset collection name, e.g. 'semantic_kitti', 'sample_kitti'",
    )
    sequence_id: str = Field(
        min_length=1,
        description="Sequence identifier, e.g. '00'",
    )
    frame_id: str = Field(
        min_length=1,
        description="Frame identifier within sequence, e.g. '000000'",
    )
    bin_path: str = Field(
        min_length=1,
        description="Filesystem path to the Velodyne HDL-64E binary (.bin) file",
    )
    label_path: Optional[str] = Field(
        default=None,
        description="Optional path to the corresponding SemanticKITTI label (.label) file",
    )
    file_size_bytes: int = Field(
        gt=0,
        description="Binary scan file size in bytes (> 0)",
    )
    point_count: int = Field(
        gt=0,
        description="Total number of 3D points in the scan (> 0)",
    )
    has_labels: bool = Field(
        default=False,
        description="True if an authentic ground-truth label file exists for this frame",
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
    
    @field_validator("dataset_type", "sequence_id", "frame_id")
    @classmethod
    def validate_identifiers(cls, v: str) -> str:
        return validate_non_empty_str(v, "identifier")


class SampleListResponse(BaseResponse):
    """Response containing discovered LiDAR dataset sample frames."""

    total_samples: int = Field(
        ge=0,
        description="Total number of discovered sample frames",
    )
    samples: List[SampleItem] = Field(
        default_factory=list,
        description="List of discovered sample frame metadata",
    )
