"""
System health and runtime status schemas.

Provides diagnostics for API service status, PyTorch compute devices, CUDA availability,
and semantic segmentation checkpoint weights status.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.backend.schemas.common import BaseResponse


class DeviceInfo(BaseModel):
    """Host environment device and runtime platform details."""

    device_type: str = Field(description="Active compute device type, e.g. 'cuda' or 'cpu'")
    device_name: str = Field(description="Hardware model name, e.g. 'NVIDIA GeForce RTX 3080' or 'CPU'")
    torch_version: str = Field(description="Installed PyTorch package version")
    python_version: str = Field(description="Current Python runtime version")

    model_config = ConfigDict(extra="forbid")


class CudaStatus(BaseModel):
    """NVIDIA CUDA driver and GPU availability status."""

    is_available: bool = Field(description="True if torch.cuda.is_available() is True")
    device_count: int = Field(ge=0, description="Total number of visible CUDA GPUs")
    device_name: Optional[str] = Field(
        default=None,
        description="Name of the primary active CUDA GPU device if available",
    )
    cuda_version: Optional[str] = Field(
        default=None,
        description="CUDA compilation version reported by PyTorch",
    )

    model_config = ConfigDict(extra="forbid")


class CheckpointStatus(BaseModel):
    """LiDAR segmentation model weights checkpoint status."""

    checkpoint_path: str = Field(description="Filesystem path to model checkpoint (.pt/.pth)")
    exists: bool = Field(description="True if checkpoint file exists on disk")
    size_bytes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Checkpoint file size in bytes if available",
    )
    is_loaded: bool = Field(
        default=False,
        description="True if model weights are actively loaded in memory",
    )
    model_type: Optional[str] = Field(
        default="RandLA-Net",
        description="Model architecture family",
    )

    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseResponse):
    """Comprehensive system health and readiness status."""

    status: str = Field(
        default="healthy",
        description="Overall service operational health status: 'healthy', 'degraded', or 'unhealthy'",
    )
    version: str = Field(default="1.0.0", description="Backend service API version")
    uptime_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Service process uptime in seconds",
    )
    device_info: DeviceInfo = Field(description="Host compute device details")
    cuda_status: CudaStatus = Field(description="CUDA hardware acceleration status")
    checkpoint_status: CheckpointStatus = Field(description="Model weights checkpoint availability")
