"""
Backend configuration module.

Provides project-root-relative paths, checkpoint selection with fallback,
data directory locations, device detection, and environment variable overrides.
Does not use hardcoded absolute paths.
"""

import os
from pathlib import Path
from typing import List, Optional
import torch


# Project root relative to this file: src/backend/config.py -> 3 levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Checkpoint paths
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
PREFERRED_CHECKPOINT = CHECKPOINTS_DIR / "best_randlanet_real.pt"
FALLBACK_CHECKPOINT = CHECKPOINTS_DIR / "best_randlanet.pt"


def get_checkpoint_path() -> Path:
    """
    Resolve model checkpoint path with precedence:
    1. Environment variable LIDAR_CHECKPOINT_PATH (if set and exists)
    2. checkpoints/best_randlanet_real.pt (if exists)
    3. checkpoints/best_randlanet.pt (if exists)
    4. Default preferred checkpoint path (for reporting existence)
    """
    env_ckpt = os.getenv("LIDAR_CHECKPOINT_PATH")
    if env_ckpt:
        p = Path(env_ckpt)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return p

    if PREFERRED_CHECKPOINT.is_file():
        return PREFERRED_CHECKPOINT
    elif FALLBACK_CHECKPOINT.is_file():
        return FALLBACK_CHECKPOINT
    return PREFERRED_CHECKPOINT


# Data directories
DATA_DIR = Path(os.getenv("LIDAR_DATA_DIR", str(PROJECT_ROOT / "data")))
if not DATA_DIR.is_absolute():
    DATA_DIR = PROJECT_ROOT / DATA_DIR

SEMANTIC_KITTI_DIR = DATA_DIR / "semantic_kitti"
SAMPLE_KITTI_DIR = DATA_DIR / "sample_kitti"

SAMPLE_DIRS: List[Path] = [
    SEMANTIC_KITTI_DIR,
    SAMPLE_KITTI_DIR,
]


def get_compute_device() -> torch.device:
    """
    Select active compute device:
    1. Environment variable LIDAR_DEVICE if specified ('cuda' or 'cpu')
    2. CUDA if available
    3. CPU fallback
    """
    env_device = os.getenv("LIDAR_DEVICE")
    if env_device:
        return torch.device(env_device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# API service metadata
API_TITLE = "Adaptive Variable-Resolution 2.5D LiDAR Mapping API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Backend REST API for LiDAR point-cloud semantic perception, "
    "sample frame discovery, and variable-resolution 2.5D grid mapping."
)
