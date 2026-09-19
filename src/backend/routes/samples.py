"""
Dataset sample frame routes.

Provides:
- GET /api/v1/samples: list discovered LiDAR point cloud scans
- GET /api/v1/samples/{sample_id}: retrieve metadata for a single frame
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from src.backend.services.sample_service import SampleService
from src.backend.utils.errors import SampleNotFoundError, SecurityError

router = APIRouter(prefix="/api/v1", tags=["Samples"])
sample_service = SampleService()


@router.get("/samples", status_code=status.HTTP_200_OK)
def list_samples() -> List[Dict[str, Any]]:
    """
    List all discovered LiDAR point cloud frame samples from configured dataset directories.
    """
    return sample_service.list_samples()


@router.get("/samples/{sample_id}", status_code=status.HTTP_200_OK)
def get_sample_by_id(sample_id: str) -> Dict[str, Any]:
    """
    Retrieve scan metadata for a specific sample frame by sample_id.
    """
    try:
        return sample_service.get_sample(sample_id)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
