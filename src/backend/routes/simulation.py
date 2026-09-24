"""
Simulation frame route for LiDAR Adaptive Variable-Resolution Perception Workstation.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from src.frontend.providers.simulation_provider import SimulationDataProvider

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])
_provider = SimulationDataProvider(seed=42)


@router.get("/frames", status_code=status.HTTP_200_OK)
def get_simulation_frames() -> List[Dict[str, Any]]:
    """Return available deterministic simulation frames."""
    return _provider.get_available_frames()


@router.get("/frame/{frame_id}", status_code=status.HTTP_200_OK)
def get_simulation_frame_data(frame_id: str) -> Dict[str, Any]:
    """Return full simulation perception and mapping bundle for a frame."""
    perc = _provider.get_perception_data(frame_id)
    ada = _provider.get_adaptive_map(perc)
    uni = _provider.get_uniform_map(perc)
    comp = _provider.get_map_comparison(uni, ada)
    elev = _provider.get_elevation_profile(frame_id)
    perf = _provider.get_performance_metrics(frame_id)
    logs = _provider.get_system_logs(frame_id)
    objs = _provider.get_scene_objects(frame_id)

    return {
        "perception": perc,
        "adaptive_map": ada,
        "uniform_map": uni,
        "comparison": comp,
        "elevation_profile": elev,
        "performance": perf,
        "logs": logs,
        "scene_objects": objs,
    }
