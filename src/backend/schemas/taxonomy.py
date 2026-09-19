"""
Semantic taxonomy schemas and project class definitions.

Defines the project's 8-class taxonomy, color mappings (RGB float, uint8, and hex),
and recommended 2.5D grid cell resolutions for adaptive mapping.
"""

from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.backend.schemas.common import BaseResponse


class ColorInfo(BaseModel):
    """Multi-format color representation for rendering and visualization."""

    rgb_float: List[float] = Field(
        description="Normalized RGB color components in range [0.0, 1.0]",
    )
    rgb_uint8: List[int] = Field(
        description="Integer RGB color components in range [0, 255]",
    )
    hex_code: str = Field(
        description="Hexadecimal color string representation, e.g. '#7f3f7f'",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("rgb_float")
    @classmethod
    def validate_rgb_float(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"rgb_float must contain exactly 3 components (R, G, B), got {len(v)}")
        for component in v:
            if not (0.0 <= component <= 1.0):
                raise ValueError(f"RGB float component {component} must be in range [0.0, 1.0]")
        return v

    @field_validator("rgb_uint8")
    @classmethod
    def validate_rgb_uint8(cls, v: List[int]) -> List[int]:
        if len(v) != 3:
            raise ValueError(f"rgb_uint8 must contain exactly 3 components (R, G, B), got {len(v)}")
        for component in v:
            if not (0 <= component <= 255):
                raise ValueError(f"RGB uint8 component {component} must be in range [0, 255]")
        return v

    @field_validator("hex_code")
    @classmethod
    def validate_hex_code(cls, v: str) -> str:
        s = v.strip()
        if not s.startswith("#") or len(s) != 7:
            raise ValueError(f"hex_code must be a 7-character string formatted as '#rrggbb', got '{v}'")
        try:
            int(s[1:], 16)
        except ValueError:
            raise ValueError(f"hex_code contains invalid hex characters: '{v}'")
        return s.lower()


class ClassTaxonomyItem(BaseModel):
    """A semantic class within the project's 8-class taxonomy."""

    class_id: int = Field(ge=0, le=7, description="Project semantic class ID (0 to 7)")
    name: str = Field(min_length=1, description="Semantic class identifier name")
    priority: str = Field(description="Perception and mapping priority description")
    color: ColorInfo = Field(description="RGB and hex color representation")
    recommended_resolution_m: float = Field(
        gt=0.0,
        description="Recommended grid cell resolution in meters for adaptive mapping",
    )

    model_config = ConfigDict(extra="forbid")


class TaxonomyResponse(BaseResponse):
    """Response containing the complete project taxonomy."""

    num_classes: int = Field(default=8, ge=8, le=8, description="Number of semantic classes (fixed at 8)")
    classes: List[ClassTaxonomyItem] = Field(
        description="Complete list of the 8 canonical semantic classes",
    )


# Canonical project 8-class taxonomy definitions matching Member 1 and docs/MEMBER2_HANDOFF_GUIDE.md
PROJECT_TAXONOMY_ITEMS: List[ClassTaxonomyItem] = [
    ClassTaxonomyItem(
        class_id=0,
        name="road",
        priority="Ground Base",
        color=ColorInfo(
            rgb_float=[0.50, 0.25, 0.50],
            rgb_uint8=[127, 63, 127],
            hex_code="#7f3f7f",
        ),
        recommended_resolution_m=0.40,
    ),
    ClassTaxonomyItem(
        class_id=1,
        name="sidewalk",
        priority="Boundary",
        color=ColorInfo(
            rgb_float=[0.96, 0.14, 0.59],
            rgb_uint8=[244, 35, 150],
            hex_code="#f42396",
        ),
        recommended_resolution_m=0.20,
    ),
    ClassTaxonomyItem(
        class_id=2,
        name="building",
        priority="Static Barrier",
        color=ColorInfo(
            rgb_float=[0.35, 0.35, 0.35],
            rgb_uint8=[89, 89, 89],
            hex_code="#595959",
        ),
        recommended_resolution_m=0.50,
    ),
    ClassTaxonomyItem(
        class_id=3,
        name="vegetation",
        priority="Soft Obstacle",
        color=ColorInfo(
            rgb_float=[0.22, 0.60, 0.22],
            rgb_uint8=[56, 153, 56],
            hex_code="#389938",
        ),
        recommended_resolution_m=0.30,
    ),
    ClassTaxonomyItem(
        class_id=4,
        name="vehicle",
        priority="Dynamic Critical",
        color=ColorInfo(
            rgb_float=[0.20, 0.50, 0.90],
            rgb_uint8=[51, 127, 229],
            hex_code="#337fe5",
        ),
        recommended_resolution_m=0.10,
    ),
    ClassTaxonomyItem(
        class_id=5,
        name="pedestrian",
        priority="Ultra-Critical",
        color=ColorInfo(
            rgb_float=[0.90, 0.15, 0.15],
            rgb_uint8=[229, 38, 38],
            hex_code="#e52626",
        ),
        recommended_resolution_m=0.05,
    ),
    ClassTaxonomyItem(
        class_id=6,
        name="pole_sign",
        priority="Vertical Obstacle",
        color=ColorInfo(
            rgb_float=[1.00, 0.85, 0.10],
            rgb_uint8=[255, 216, 25],
            hex_code="#ffd819",
        ),
        recommended_resolution_m=0.10,
    ),
    ClassTaxonomyItem(
        class_id=7,
        name="other",
        priority="Noise / Default",
        color=ColorInfo(
            rgb_float=[0.65, 0.65, 0.65],
            rgb_uint8=[165, 165, 165],
            hex_code="#a5a5a5",
        ),
        recommended_resolution_m=0.40,
    ),
]

PROJECT_TAXONOMY_MAP: Dict[int, ClassTaxonomyItem] = {
    item.class_id: item for item in PROJECT_TAXONOMY_ITEMS
}


def get_taxonomy_response() -> TaxonomyResponse:
    """Return a pre-populated TaxonomyResponse with all 8 project classes."""
    return TaxonomyResponse(
        num_classes=len(PROJECT_TAXONOMY_ITEMS),
        classes=list(PROJECT_TAXONOMY_ITEMS),
    )


def get_class_taxonomy(class_id: int) -> ClassTaxonomyItem:
    """Retrieve taxonomy definition for a specific class ID in [0, 7]."""
    if class_id not in PROJECT_TAXONOMY_MAP:
        raise ValueError(f"Invalid class ID {class_id}. Must be between 0 and 7.")
    return PROJECT_TAXONOMY_MAP[class_id]
