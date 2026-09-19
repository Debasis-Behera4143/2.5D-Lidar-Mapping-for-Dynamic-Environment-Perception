"""
Backend schemas package.

Exports all Pydantic V2 data contracts for health diagnostics, taxonomy definitions,
sample discovery, perception inference, adaptive 2.5D mapping, and performance metrics.
"""

from src.backend.schemas.common import (
    BaseResponse,
    ErrorDetail,
    ErrorResponse,
    ROIBounds,
    SpatialBounds,
    SuccessResponse,
    validate_non_empty_str,
)
from src.backend.schemas.health import (
    CheckpointStatus,
    CudaStatus,
    DeviceInfo,
    HealthResponse,
)
from src.backend.schemas.inference import (
    ConfidenceSummary,
    InferenceEvaluationInfo,
    InferenceRequest,
    InferenceResponse,
    PointPreviewItem,
)
from src.backend.schemas.mapping import (
    GridCellPreview,
    MappingRequest,
    MappingResponse,
    MemoryEstimate,
)
from src.backend.schemas.metrics import MetricsResponse
from src.backend.schemas.sample import (
    SampleItem,
    SampleListResponse,
)
from src.backend.schemas.taxonomy import (
    PROJECT_TAXONOMY_ITEMS,
    PROJECT_TAXONOMY_MAP,
    ClassTaxonomyItem,
    ColorInfo,
    TaxonomyResponse,
    get_class_taxonomy,
    get_taxonomy_response,
)

__all__ = [
    # Common
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    "SpatialBounds",
    "ROIBounds",
    "validate_non_empty_str",
    # Health
    "DeviceInfo",
    "CudaStatus",
    "CheckpointStatus",
    "HealthResponse",
    # Taxonomy
    "ColorInfo",
    "ClassTaxonomyItem",
    "TaxonomyResponse",
    "PROJECT_TAXONOMY_ITEMS",
    "PROJECT_TAXONOMY_MAP",
    "get_taxonomy_response",
    "get_class_taxonomy",
    # Sample
    "SampleItem",
    "SampleListResponse",
    # Inference
    "InferenceRequest",
    "ConfidenceSummary",
    "PointPreviewItem",
    "InferenceEvaluationInfo",
    "InferenceResponse",
    # Mapping
    "MappingRequest",
    "MemoryEstimate",
    "GridCellPreview",
    "MappingResponse",
    # Metrics
    "MetricsResponse",
]
