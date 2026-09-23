"""
Frontend REST API Client.

Provides a robust, typed client interface communicating with the FastAPI backend:
- /api/v1/health
- /api/v1/classes
- /api/v1/samples
- /api/v1/samples/{sample_id}
- /api/v1/inference
- /api/v1/map/uniform
- /api/v1/map/adaptive
- /api/v1/map/compare
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union
import httpx

from src.frontend.config import (
    API_TIMEOUT_SECONDS,
    BACKEND_API_URL,
    CANONICAL_TAXONOMY,
)


class ApiClient:
    """
    HTTP Client for the LiDAR Perception & 2.5D Mapping Backend.
    """

    def __init__(self, base_url: str = BACKEND_API_URL, timeout: float = API_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def check_health(self) -> Dict[str, Any]:
        """
        Check backend system health, device info, and checkpoint availability.
        """
        try:
            start_t = time.perf_counter()
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self._url("/api/v1/health"))
                latency_ms = round((time.perf_counter() - start_t) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    data["online"] = True
                    data["ping_ms"] = latency_ms
                    return data
                return {
                    "online": False,
                    "status": "degraded",
                    "error": f"HTTP {resp.status_code}: {resp.text}",
                    "ping_ms": latency_ms,
                }
        except httpx.ConnectError:
            return {
                "online": False,
                "status": "offline",
                "error": "Backend offline. FastAPI service could not be reached.",
                "ping_ms": None,
            }
        except Exception as e:
            return {
                "online": False,
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "ping_ms": None,
            }

    def get_classes(self) -> List[Dict[str, Any]]:
        """
        Retrieve 8-class taxonomy definitions from backend or fallback to canonical definition.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self._url("/api/v1/classes"))
                if resp.status_code == 200:
                    return resp.json().get("classes", CANONICAL_TAXONOMY)
        except Exception:
            pass
        return CANONICAL_TAXONOMY

    def get_samples(self) -> List[Dict[str, Any]]:
        """
        List all discovered LiDAR frame scans (.bin and .label).
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self._url("/api/v1/samples"))
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return []

    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve scan metadata for a specific sample frame by sample_id.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self._url(f"/api/v1/samples/{sample_id}"))
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return None

    def run_inference(
        self,
        bin_path: str,
        label_path: Optional[str] = None,
        num_points: int = 4096,
        interpolate_to_full: bool = False,
        preview_points_limit: int = 2000,
    ) -> Dict[str, Any]:
        """
        Run semantic segmentation inference on a binary LiDAR scan (.bin).
        """
        payload = {
            "bin_path": bin_path,
            "label_path": label_path,
            "num_points": int(num_points),
            "interpolate_to_full": bool(interpolate_to_full),
            "preview_points_limit": int(preview_points_limit),
        }
        start_t = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._url("/api/v1/inference"), json=payload)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    data["_client_latency_ms"] = round(elapsed_ms, 2)
                    data["_success"] = True
                    return data
                return {
                    "_success": False,
                    "error": resp.json().get("detail", f"Inference failed with HTTP {resp.status_code}"),
                    "status_code": resp.status_code,
                    "_client_latency_ms": round(elapsed_ms, 2),
                }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return {
                "_success": False,
                "error": f"Connection error: {type(e).__name__}: {str(e)}",
                "_client_latency_ms": round(elapsed_ms, 2),
            }

    def generate_uniform_map(
        self,
        perception_payload: Dict[str, Any],
        resolution: float = 0.50,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate uniform 2.5D grid map.
        """
        body = {
            "perception": perception_payload,
            "resolution": float(resolution),
            "roi_bounds": list(roi_bounds) if roi_bounds is not None else None,
        }
        start_t = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._url("/api/v1/map/uniform"), json=body)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    data["_client_latency_ms"] = round(elapsed_ms, 2)
                    data["_success"] = True
                    return data
                return {
                    "_success": False,
                    "error": resp.json().get("detail", f"Uniform mapping failed with HTTP {resp.status_code}"),
                    "status_code": resp.status_code,
                    "_client_latency_ms": round(elapsed_ms, 2),
                }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return {
                "_success": False,
                "error": f"Uniform mapping error: {type(e).__name__}: {str(e)}",
                "_client_latency_ms": round(elapsed_ms, 2),
            }

    def generate_adaptive_map(
        self,
        perception_payload: Dict[str, Any],
        previous_payload: Optional[Dict[str, Any]] = None,
        base_resolution: float = 1.00,
        fine_resolution: float = 0.25,
        importance_threshold: float = 0.50,
        dynamic_threshold: float = 0.25,
        roi_bounds: Optional[Tuple[float, ...]] = None,
    ) -> Dict[str, Any]:
        """
        Generate adaptive variable-resolution 2.5D grid map.
        """
        body = {
            "perception": perception_payload,
            "previous_perception": previous_payload,
            "base_resolution": float(base_resolution),
            "fine_resolution": float(fine_resolution),
            "importance_threshold": float(importance_threshold),
            "dynamic_threshold": float(dynamic_threshold),
            "roi_bounds": list(roi_bounds) if roi_bounds is not None else None,
        }
        start_t = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._url("/api/v1/map/adaptive"), json=body)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    data["_client_latency_ms"] = round(elapsed_ms, 2)
                    data["_success"] = True
                    return data
                return {
                    "_success": False,
                    "error": resp.json().get("detail", f"Adaptive mapping failed with HTTP {resp.status_code}"),
                    "status_code": resp.status_code,
                    "_client_latency_ms": round(elapsed_ms, 2),
                }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return {
                "_success": False,
                "error": f"Adaptive mapping error: {type(e).__name__}: {str(e)}",
                "_client_latency_ms": round(elapsed_ms, 2),
            }

    def compare_maps(
        self,
        uniform_map: Dict[str, Any],
        adaptive_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare uniform and adaptive maps and return efficiency benchmarks.
        """
        body = {
            "uniform_map": uniform_map,
            "adaptive_map": adaptive_map,
        }
        start_t = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(self._url("/api/v1/map/compare"), json=body)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    data["_client_latency_ms"] = round(elapsed_ms, 2)
                    data["_success"] = True
                    return data
                return {
                    "_success": False,
                    "error": resp.json().get("detail", f"Comparison failed with HTTP {resp.status_code}"),
                    "status_code": resp.status_code,
                    "_client_latency_ms": round(elapsed_ms, 2),
                }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return {
                "_success": False,
                "error": f"Comparison error: {type(e).__name__}: {str(e)}",
                "_client_latency_ms": round(elapsed_ms, 2),
            }
