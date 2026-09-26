"""
FastAPI application entrypoint for LiDAR Adaptive Variable-Resolution Mapping.

Registers perception, diagnostics, sample discovery, and spatial mapping routers
with safe global exception handling to prevent leaking internal stack traces.
"""

from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.backend.config import API_DESCRIPTION, API_TITLE, API_VERSION
from src.backend.routes.health import router as health_router
from src.backend.routes.inference import router as inference_router
from src.backend.routes.samples import router as samples_router
from src.backend.routes.taxonomy import router as taxonomy_router
from src.backend.routers.mapping_router import router as mapping_router
from src.backend.utils.errors import (
    BackendError,
    CheckpointNotFoundError,
    InferenceError,
    InvalidInputError,
    SampleNotFoundError,
    SecurityError,
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.backend.routes.simulation import router as simulation_router
from src.backend.routes.perception import router as perception_router

# Register route modules
app.include_router(health_router)
app.include_router(taxonomy_router)
app.include_router(samples_router)
app.include_router(inference_router)
app.include_router(perception_router)
app.include_router(mapping_router)
app.include_router(simulation_router)

FRONTEND_INDEX = Path(__file__).resolve().parents[2] / "frontend" / "dist" / "index.html"


@app.get("/", status_code=status.HTTP_200_OK)
def root() -> Any:
    """
    Serve the dashboard at the public service root when the frontend is bundled.
    """
    if FRONTEND_INDEX.is_file():
        return FileResponse(FRONTEND_INDEX)

    return {
        "message": API_TITLE,
        "version": API_VERSION,
        "available_endpoints": [
            "/api/v1/health",
            "/api/v1/classes",
            "/api/v1/samples",
            "/api/v1/inference",
            "/api/v1/map/uniform",
            "/api/v1/map/adaptive",
            "/api/v1/map/compare",
            "/docs",
            "/redoc",
        ],
    }


if FRONTEND_INDEX.parent.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_INDEX.parent / "assets"), name="frontend-assets")


# Global Exception Handlers ensuring no raw stack traces leak to users


@app.exception_handler(SampleNotFoundError)
async def sample_not_found_handler(request: Request, exc: SampleNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": str(exc)},
    )


@app.exception_handler(CheckpointNotFoundError)
async def checkpoint_not_found_handler(request: Request, exc: CheckpointNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"error": "Service Unavailable", "message": str(exc)},
    )


@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"error": "Forbidden", "message": str(exc)},
    )


@app.exception_handler(InvalidInputError)
async def invalid_input_handler(request: Request, exc: InvalidInputError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "message": str(exc)},
    )


@app.exception_handler(InferenceError)
async def inference_error_handler(request: Request, exc: InferenceError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Inference Error", "message": str(exc)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg', 'Invalid input')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "details": errors},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Fallback catch-all preventing internal stack trace disclosure."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."},
    )
