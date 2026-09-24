"""
Right-Side Workstation Panels Component.

Encapsulates the 3 right-column cards matching the reference image:
1. Semantic Legend (10 classes with functional tags)
2. Object Detection / Scene Objects (Count) [SIMULATION]
3. Adaptive Grid Resolution Guide (Distance vs cell size bands)
"""

from typing import Any, Dict, Optional
import streamlit as st

from src.frontend.config import DISPLAY_TAXONOMY


def render_semantic_legend_widget() -> None:
    """
    Render 10-class semantic taxonomy legend matching reference image.
    """
    st.markdown(
        '<div class="viewer-header">'
        '<div class="viewer-title">Semantic Legend</div>'
        '<span class="viewer-tag">10 Classes</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    rows_html = []
    for item in DISPLAY_TAXONOMY:
        name = item["name"]
        color = item["color"]
        rows_html.append(
            '<div class="legend-row">'
            '<div style="display: flex; align-items: center;">'
            f'<span class="legend-color-box" style="background-color: {color};"></span>'
            f'<span style="color: #ffffff; font-weight: 500;">{name}</span>'
            '</div>'
            '</div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def render_scene_objects_widget(
    scene_objects: Optional[Dict[str, int]] = None,
    is_simulation: bool = True,
) -> None:
    """
    Render Object Detection (Count) card with explicit SIMULATION provenance.
    """
    counts = scene_objects or {
        "Vehicle": 3,
        "Pedestrian": 2,
        "Motorcycle": 0,
        "Bicycle": 1,
        "Static (Pole/Sign)": 4,
        "Others": 1,
    }

    badge_html = (
        '<span class="metric-badge badge-simulation">SIMULATION</span>'
        if is_simulation
        else '<span class="metric-badge badge-measured">MEASURED</span>'
    )

    icons = {
        "Vehicle": "🚗",
        "Pedestrian": "🚶",
        "Motorcycle": "🏍️",
        "Bicycle": "🚲",
        "Static (Pole/Sign)": "📍",
        "Others": "📦",
    }

    st.markdown(
        '<div class="viewer-header" style="margin-top: 0.65rem;">'
        f'<div class="viewer-title">Object Detection (Count)</div>'
        f'{badge_html}'
        '</div>',
        unsafe_allow_html=True,
    )

    rows_html = []
    for obj_name, cnt in counts.items():
        icon = icons.get(obj_name, "🔹")
        rows_html.append(
            '<div class="object-row">'
            '<div style="display: flex; align-items: center; gap: 0.45rem;">'
            f'<span>{icon}</span>'
            f'<span style="color: #e2e8f0; font-weight: 500;">{obj_name}</span>'
            '</div>'
            f'<span class="object-count-badge">{cnt}</span>'
            '</div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def render_adaptive_grid_resolution_widget() -> None:
    """
    Render Adaptive Grid Resolution guide visualizing distance-dependent cell sizes.
    """
    st.markdown(
        '<div class="viewer-header" style="margin-top: 0.65rem;">'
        '<div class="viewer-title">Adaptive Grid Resolution</div>'
        '<span class="viewer-tag" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.35);">4 Bands</span>'
        '</div>'
        '<div class="grid-res-row res-band-blue">'
        '<span>0 – 10 m</span>'
        '<span>(5 cm)</span>'
        '</div>'
        '<div class="grid-res-row res-band-purple">'
        '<span>10 – 25 m</span>'
        '<span>(10 cm)</span>'
        '</div>'
        '<div class="grid-res-row res-band-yellow">'
        '<span>25 – 50 m</span>'
        '<span>(25 cm)</span>'
        '</div>'
        '<div class="grid-res-row res-band-red">'
        '<span>50 – 100 m</span>'
        '<span>(50 cm)</span>'
        '</div>'
        '<div style="font-size: 0.68rem; color: #64748b; margin-top: 0.25rem; line-height: 1.35;">'
        '<strong style="color: #94a3b8;">Near / Dynamic:</strong> Fine 5cm detail<br>'
        '<strong style="color: #94a3b8;">Far / Static:</strong> Coarser 50cm detail'
        '</div>',
        unsafe_allow_html=True,
    )


def render_right_column_panels(
    scene_objects: Optional[Dict[str, int]] = None,
    is_simulation: bool = True,
) -> None:
    """
    Render the combined right-column stack.
    """
    render_semantic_legend_widget()
    render_scene_objects_widget(scene_objects=scene_objects, is_simulation=is_simulation)
    render_adaptive_grid_resolution_widget()
