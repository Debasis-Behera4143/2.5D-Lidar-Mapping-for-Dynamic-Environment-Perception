"""
Frontend configuration module.

Defines API service endpoints, default algorithmic hyperparameters,
visualization downsampling limits, and canonical color palettes.
"""

import os
from pathlib import Path
from typing import Dict, List

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

# 8 Canonical Project Semantic Classes with fallback hex and RGB definitions
# (Synchronized with src/ai/label_mapping.py and src/backend/schemas/taxonomy.py)
CANONICAL_TAXONOMY: List[Dict[str, str]] = [
    {"id": 0, "name": "road", "color": "#7f3f7f", "priority": "Ground Base", "resolution": 0.40},
    {"id": 1, "name": "sidewalk", "color": "#f42396", "priority": "Boundary", "resolution": 0.20},
    {"id": 2, "name": "building", "color": "#595959", "priority": "Static Barrier", "resolution": 0.50},
    {"id": 3, "name": "vegetation", "color": "#389938", "priority": "Soft Obstacle", "resolution": 0.30},
    {"id": 4, "name": "vehicle", "color": "#337fe5", "priority": "Dynamic Critical", "resolution": 0.10},
    {"id": 5, "name": "pedestrian", "color": "#e52626", "priority": "Ultra-Critical", "resolution": 0.05},
    {"id": 6, "name": "pole_sign", "color": "#ffd819", "priority": "Vertical Obstacle", "resolution": 0.10},
    {"id": 7, "name": "other", "color": "#a5a5a5", "priority": "Noise / Default", "resolution": 0.40},
]

CLASS_COLORS: Dict[int, str] = {item["id"]: item["color"] for item in CANONICAL_TAXONOMY}
CLASS_NAMES: Dict[int, str] = {item["id"]: item["name"] for item in CANONICAL_TAXONOMY}

# Navigation Pages
PAGES = [
    "Dashboard",
    "Point Cloud Viewer",
    "2.5D Mapping",
    "Semantic View",
    "Terrain Analysis",
    "Object Analysis",
    "Performance",
    "Settings",
]
