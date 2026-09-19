"""
Backend services package.

Provides services for inference, dataset sample discovery, JSON serialization,
and spatial grid mapping.
"""

from src.backend.services.inference_service import InferenceService
from src.backend.services.mapping_service import MappingService
from src.backend.services.sample_service import SampleService
from src.backend.services.serialization import to_json_safe

__all__ = [
    "InferenceService",
    "SampleService",
    "MappingService",
    "to_json_safe",
]
