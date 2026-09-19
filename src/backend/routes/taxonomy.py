"""
Semantic taxonomy definitions route.

Provides GET /api/v1/classes returning the canonical 8-class taxonomy,
color codes, and recommended 2.5D grid cell resolutions.
"""

from fastapi import APIRouter, status

from src.backend.schemas.taxonomy import TaxonomyResponse, get_taxonomy_response

router = APIRouter(prefix="/api/v1", tags=["Taxonomy"])


@router.get("/classes", response_model=TaxonomyResponse, status_code=status.HTTP_200_OK)
def get_classes() -> TaxonomyResponse:
    """
    Retrieve the project's 8 semantic classes with color codes and recommended cell resolutions.
    """
    return get_taxonomy_response()
