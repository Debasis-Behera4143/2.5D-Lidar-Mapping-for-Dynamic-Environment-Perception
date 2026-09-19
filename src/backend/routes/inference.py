"""
Perception inference route endpoint.

Provides POST /api/v1/inference executing semantic segmentation on LiDAR scans.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from src.backend.schemas.inference import InferenceRequest, InferenceResponse
from src.backend.services.inference_service import InferenceService
from src.backend.services.serialization import to_json_safe
from src.backend.utils.errors import (
    CheckpointNotFoundError,
    InferenceError,
    InvalidInputError,
    SampleNotFoundError,
    SecurityError,
)

router = APIRouter(prefix="/api/v1", tags=["Inference"])
inference_service = InferenceService()


@router.post("/inference", status_code=status.HTTP_200_OK)
def run_inference(req: InferenceRequest) -> Dict[str, Any]:
    """
    Run semantic segmentation inference on a binary LiDAR point cloud (.bin).
    """
    try:
        result = inference_service.run_inference(
            bin_path=req.bin_path,
            label_path=req.label_path,
            num_points=req.num_points,
            interpolate_to_full=req.interpolate_to_full,
            preview_points_limit=req.preview_points_limit,
        )
        return to_json_safe(result)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CheckpointNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except (InvalidInputError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InferenceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {type(e).__name__}: {e}",
        )
