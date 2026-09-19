"""
Backend API routes package.
"""

from src.backend.routes.health import router as health_router
from src.backend.routes.inference import router as inference_router
from src.backend.routes.samples import router as samples_router
from src.backend.routes.taxonomy import router as taxonomy_router

__all__ = [
    "health_router",
    "taxonomy_router",
    "samples_router",
    "inference_router",
]
