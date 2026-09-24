"""
Frontend configuration module.

Defines API service endpoints, default algorithmic hyperparameters,
visualization downsampling limits, and canonical color palettes.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "30.0"))

# Default Mapping Hyperparameters
DEFAULT_BASE_RESOLUTION: float = 1.00       # Coarse cell resolution in meters
DEFAULT_FINE_RESOLUTION: float = 0.25       # Fine cell resolution in meters
DEFAULT_IMPORTANCE_THRESHOLD: float = 0.50  # Cutoff to trigger coarse->fine cell subdivision
DEFAULT_DYNAMIC_THRESHOLD: float = 0.25     # Point displacement threshold (meters)
DEFAULT_NUM_POINTS: int = 4096              # Default subsampled point cloud size for inference
DEFAULT_PREVIEW_POINTS: int = 4000          # Downsampling limit for interactive 3D WebGL rendering

# 8 Canonical Project Semantic Classes with unified technical palettes
# (Synchronized with src/ai/label_mapping.py and src/backend/schemas/taxonomy.py)
CANONICAL_TAXONOMY: List[Dict[str, str]] = [
    {"id": 0, "name": "road", "color": "#2563eb", "priority": "Drivable Road", "resolution": 0.05},
    {"id": 1, "name": "sidewalk", "color": "#8b5cf6", "priority": "Drivable / Walkable", "resolution": 0.10},
    {"id": 2, "name": "building", "color": "#ef4444", "priority": "Non-drivable Wall", "resolution": 0.25},
    {"id": 3, "name": "vegetation", "color": "#10b981", "priority": "Non-drivable Soft", "resolution": 0.50},
    {"id": 4, "name": "vehicle", "color": "#d946ef", "priority": "Dynamic Vehicle", "resolution": 0.05},
    {"id": 5, "name": "pedestrian", "color": "#eab308", "priority": "Dynamic Pedestrian", "resolution": 0.05},
    {"id": 6, "name": "pole_sign", "color": "#06b6d4", "priority": "Non-drivable Vertical", "resolution": 0.10},
    {"id": 7, "name": "other", "color": "#64748b", "priority": "Ground / Other", "resolution": 0.50},
]

# 10 Extended Visual/Dashboard Classes matching Reference Image and Prompt Section 9
DISPLAY_TAXONOMY: List[Dict[str, Any]] = [
    {"id": 0, "name": "Road (Drivable)", "color": "#2563eb", "tag": "Drivable", "short": "road"},
    {"id": 1, "name": "Sidewalk (Drivable)", "color": "#8b5cf6", "tag": "Drivable", "short": "sidewalk"},
    {"id": 2, "name": "Building / Wall (Non-drivable)", "color": "#ef4444", "tag": "Non-drivable", "short": "building"},
    {"id": 3, "name": "Vegetation (Non-drivable)", "color": "#10b981", "tag": "Non-drivable", "short": "vegetation"},
    {"id": 4, "name": "Vehicle (Dynamic)", "color": "#d946ef", "tag": "Dynamic", "short": "vehicle"},
    {"id": 5, "name": "Pedestrian (Dynamic)", "color": "#eab308", "tag": "Dynamic", "short": "pedestrian"},
    {"id": 6, "name": "Pole / Sign (Non-drivable)", "color": "#06b6d4", "tag": "Non-drivable", "short": "pole_sign"},
    {"id": 7, "name": "Ground / Terrain (Drivable)", "color": "#f97316", "tag": "Drivable", "short": "terrain"},
    {"id": 8, "name": "Barrier (Non-drivable)", "color": "#b45309", "tag": "Non-drivable", "short": "barrier"},
    {"id": 9, "name": "Other", "color": "#64748b", "tag": "Neutral", "short": "other"},
]

CLASS_COLORS: Dict[int, str] = {item["id"]: item["color"] for item in CANONICAL_TAXONOMY}
CLASS_COLORS.update({7: "#f97316", 8: "#b45309", 9: "#64748b"})

CLASS_NAMES: Dict[int, str] = {item["id"]: item["name"] for item in CANONICAL_TAXONOMY}
CLASS_NAMES.update({7: "terrain", 8: "barrier", 9: "other"})

DISPLAY_CLASS_COLORS: Dict[int, str] = {item["id"]: item["color"] for item in DISPLAY_TAXONOMY}
DISPLAY_CLASS_NAMES: Dict[int, str] = {item["id"]: item["name"] for item in DISPLAY_TAXONOMY}

# Core Navigation Pages (Consolidated to essential research workflows)
PAGES = [
    "Dashboard",
    "Point Cloud Viewer",
    "2.5D Mapping",
    "Semantic Analysis",
    "Performance",
    "Settings",
]

