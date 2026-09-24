"""
Abstract Base Data Provider.

Defines unified interface for both simulation data and real FastAPI responses,
allowing the presentation layer and visualization components to be completely agnostic
to the data source.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseDataProvider(ABC):
    """
    Abstract interface for LiDAR perception, 2.5D mapping, and diagnostics data.
    """

    @abstractmethod
    def get_source_type(self) -> str:
        """Return 'Simulation' or 'FastAPI'."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Check connection / readiness state."""
        pass

    @abstractmethod
    def get_available_frames(self) -> List[Dict[str, Any]]:
        """Return list of selectable sample frames or simulated scenes."""
        pass

    @abstractmethod
    def get_perception_data(self, frame_id: str = "1248", **kwargs) -> Dict[str, Any]:
        """
        Fetch or compute 3D point cloud with semantic labels, confidences,
        intensities, and bounding boxes.
        """
        pass

    @abstractmethod
    def get_adaptive_map(
        self,
        perception_payload: Dict[str, Any],
        base_resolution: float = 0.50,
        fine_resolution: float = 0.10,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate or fetch adaptive variable-resolution 2.5D grid map.
        """
        pass

    @abstractmethod
    def get_uniform_map(
        self,
        perception_payload: Dict[str, Any],
        resolution: float = 0.10,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate or fetch uniform grid map for benchmark comparison.
        """
        pass

    @abstractmethod
    def get_map_comparison(
        self,
        uniform_map: Dict[str, Any],
        adaptive_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute or retrieve comparative efficiency metrics (cells, memory, latency).
        """
        pass

    @abstractmethod
    def get_elevation_profile(self, frame_id: str = "1248") -> Dict[str, Any]:
        """
        Retrieve 1D longitudinal/transverse elevation contour (distance vs height).
        """
        pass

    @abstractmethod
    def get_performance_metrics(self, frame_id: str = "1248") -> Dict[str, Any]:
        """
        Retrieve mIoU, FPS, Latency, and Memory metrics (explicitly labeled provenance).
        """
        pass

    @abstractmethod
    def get_system_logs(self, frame_id: str = "1248") -> List[Dict[str, str]]:
        """
        Retrieve system timeline event logs.
        """
        pass

    @abstractmethod
    def get_scene_objects(self, frame_id: str = "1248") -> Dict[str, int]:
        """
        Retrieve count of detected scene objects.
        """
        pass

    @abstractmethod
    def get_annotations(self, frame_id: str = "1248") -> List[Dict[str, Any]]:
        """
        Retrieve 3D spatial callout annotations with leader positions.
        """
        pass
