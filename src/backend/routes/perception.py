"""
3D Spatial LiDAR Perception & Object Detection Route.

Provides:
- POST /api/v1/perception: Extracts 3D object instances, calculates bounding boxes,
  ranges, ego-centric angular sectors, forward obstacles, and proximity alerts.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import numpy as np

from src.ai.instance_clustering import InstancePerceptionEngine
from src.backend.services.inference_service import InferenceService
from src.backend.services.serialization import to_json_safe
from src.backend.utils.errors import SampleNotFoundError

router = APIRouter(prefix="/api/v1", tags=["Perception"])
inference_service = InferenceService()


class PerceptionRequest(BaseModel):
    """Payload for 3D instance perception analysis."""
    bin_path: Optional[str] = Field(default=None, description="Optional path to .bin scan")
    label_path: Optional[str] = Field(default=None, description="Optional path to .label file")
    perception: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw perception dictionary with points and predicted_labels")
    front_angle_deg: float = Field(default=30.0, ge=5.0, le=90.0, description="Forward field of view cone half-angle in degrees")
    front_range_m: float = Field(default=60.0, gt=0.0, description="Max forward detection range in meters")


@router.post("/perception", status_code=status.HTTP_200_OK)
def analyze_perception(req: PerceptionRequest) -> Dict[str, Any]:
    """
    Run 3D instance perception: extract objects, bounding boxes, distances,
    and forward collision proximity alerts.
    """
    try:
        pts = None
        lbls = None
        confs = None
        frame_id = "000000"

        if req.bin_path:
            raw_res = inference_service.run_inference(
                bin_path=req.bin_path,
                label_path=req.label_path,
                interpolate_to_full=True,
                preview_points_limit=40000,
            )
            pts = np.array(raw_res["points"])
            lbls = np.array(raw_res["predicted_labels"])
            confs = np.array(raw_res["confidence_scores"])
            frame_id = raw_res.get("frame_id", "000000")
        elif req.perception and "points" in req.perception:
            pts = np.array(req.perception["points"])
            lbls = np.array(req.perception.get("predicted_labels", []))
            confs = np.array(req.perception.get("confidence_scores", []))
            frame_id = str(req.perception.get("frame_id", "000000"))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either 'bin_path' or 'perception' dictionary containing points and labels",
            )

        if len(pts) == 0 or len(lbls) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Point cloud contains no valid points for perception processing",
            )

        result = InstancePerceptionEngine.extract_instances(
            points=pts,
            labels=lbls,
            confidences=confs if len(confs) == len(pts) else None,
            frame_id=frame_id,
            front_angle_deg=req.front_angle_deg,
            front_range_m=req.front_range_m,
        )

        return to_json_safe(result)

    except SampleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Perception analysis failed: {type(e).__name__}: {e}",
        )
