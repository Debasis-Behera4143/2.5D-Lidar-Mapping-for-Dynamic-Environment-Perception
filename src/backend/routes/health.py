"""
System health and readiness diagnostics route.

Provides GET /api/v1/health endpoint reporting PyTorch runtime, CUDA hardware
status, and semantic segmentation model weights checkpoint availability.
"""

import sys
import time
from typing import Any, Dict
from fastapi import APIRouter, status
import torch

from src.backend.config import API_VERSION, get_checkpoint_path, get_compute_device
from src.backend.schemas.health import (
    CheckpointStatus,
    CudaStatus,
    DeviceInfo,
    HealthResponse,
)
from src.backend.services.inference_service import InferenceService

router = APIRouter(prefix="/api/v1", tags=["Health"])

START_TIME = time.time()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health() -> HealthResponse:
    """
    Retrieve service operational health, hardware platform, and model checkpoint state.
    """
    device = get_compute_device()
    ckpt_path = get_checkpoint_path()

    ckpt_exists = ckpt_path.is_file()
    ckpt_size = ckpt_path.stat().st_size if ckpt_exists else None

    # Check CUDA status
    cuda_avail = torch.cuda.is_available()
    cuda_count = torch.cuda.device_count() if cuda_avail else 0
    cuda_device_name = torch.cuda.get_device_name(0) if cuda_avail and cuda_count > 0 else None
    cuda_version = torch.version.cuda if cuda_avail else None

    # Host device info
    dev_name = cuda_device_name if device.type == "cuda" else "CPU"
    device_info = DeviceInfo(
        device_type=device.type,
        device_name=dev_name,
        torch_version=torch.__version__,
        python_version=sys.version.split()[0],
    )

    cuda_status = CudaStatus(
        is_available=cuda_avail,
        device_count=cuda_count,
        device_name=cuda_device_name,
        cuda_version=cuda_version,
    )

    inference_service = InferenceService()
    checkpoint_status = CheckpointStatus(
        checkpoint_path=str(ckpt_path).replace("\\", "/"),
        exists=ckpt_exists,
        size_bytes=ckpt_size,
        is_loaded=inference_service.is_loaded(),
        model_type="RandLA-Net",
    )

    uptime = round(time.time() - START_TIME, 2)
    overall_status = "healthy" if ckpt_exists else "degraded"

    return HealthResponse(
        status=overall_status,
        version=API_VERSION,
        uptime_seconds=uptime,
        device_info=device_info,
        cuda_status=cuda_status,
        checkpoint_status=checkpoint_status,
    )
