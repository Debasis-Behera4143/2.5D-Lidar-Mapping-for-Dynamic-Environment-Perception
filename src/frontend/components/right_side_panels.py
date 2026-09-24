"""
Right-Side Workstation Panels Component.

Encapsulates the 3 right-column cards for the executive dashboard:
1. Semantic Legend (Canonical classes with functional tags & colors)
2. Semantic Point Distribution (Actual point counts & % from perception model)
3. Adaptive Grid Resolution Guide (Distance vs cell size bands)
"""

from typing import Any, Dict, Optional
import numpy as np
import streamlit as st

from src.frontend.config import CANONICAL_TAXONOMY, CLASS_COLORS, CLASS_NAMES


def render_semantic_legend_widget() -> None:
    """
    Render canonical semantic taxonomy legend with color swatches and functional roles.
    """
    st.markdown(
        '<div class="viewer-header">'
        '<div class="viewer-title">Semantic Taxonomy</div>'
        '<span class="viewer-tag">8 Classes</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    rows_html = []
    for item in CANONICAL_TAXONOMY:
        name = item["name"].capitalize()
        color = item["color"]
        priority = item["priority"]
        rows_html.append(
            '<div class="legend-row">'
            '<div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">'
            '<div style="display: flex; align-items: center;">'
            f'<span class="legend-color-box" style="background-color: {color};"></span>'
            f'<span style="color: #ffffff; font-weight: 500;">{name}</span>'
            '</div>'
            f'<span style="font-size: 0.65rem; color: #64748b; font-family: monospace;">{priority}</span>'
            '</div>'
            '</div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def render_semantic_distribution_widget(perception_data: Dict[str, Any]) -> None:
    """
    Render actual point-wise semantic distribution derived from model inference.
    """
    labels = perception_data.get("predicted_labels", [])
    total_pts = max(1, len(labels))

    # Calculate actual class frequencies directly from predicted_labels array
    class_dist: Dict[str, int] = {}
    if len(labels) > 0:
        unique, counts = np.unique(labels, return_counts=True)
        for u, c in zip(unique, counts):
            c_name = CLASS_NAMES.get(int(u), f"class_{u}")
            class_dist[c_name] = int(c)

    st.markdown(
        '<div class="viewer-header" style="margin-top: 0.65rem;">'
        '<div class="viewer-title">Point Distribution</div>'
        '<span class="viewer-tag" style="color: #38bdf8;">INFERRED</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    rows_html = []
    # Display top classes
    sorted_items = sorted(CANONICAL_TAXONOMY, key=lambda it: class_dist.get(it["name"], 0), reverse=True)
    for item in sorted_items:
        c_name = item["name"]
        color = item["color"]
        cnt = class_dist.get(c_name, 0)
        pct = (cnt / total_pts) * 100.0 if total_pts > 0 else 0.0

        rows_html.append(
            '<div class="object-row">'
            '<div style="display: flex; align-items: center; gap: 0.45rem;">'
            f'<span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; display: inline-block;"></span>'
            f'<span style="color: #e2e8f0; font-weight: 500;">{c_name.capitalize()}</span>'
            '</div>'
            f'<span class="object-count-badge" style="font-size: 0.70rem;">{pct:.1f}% ({cnt:,d})</span>'
            '</div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def render_adaptive_grid_resolution_widget() -> None:
    """
    Render Adaptive Grid Resolution guide visualizing distance-dependent cell sizes.
    """
    st.markdown(
        '<div class="viewer-header" style="margin-top: 0.65rem;">'
        '<div class="viewer-title">Adaptive Resolution Bands</div>'
        '<span class="viewer-tag" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.35);">4 BANDS</span>'
        '</div>'
        '<div class="grid-res-row res-band-blue">'
        '<span>0 – 10 m (Near Field)</span>'
        '<span><strong>5 cm</strong> [Fine]</span>'
        '</div>'
        '<div class="grid-res-row res-band-purple">'
        '<span>10 – 25 m (Mid Range)</span>'
        '<span><strong>10 cm</strong> [Mid]</span>'
        '</div>'
        '<div class="grid-res-row res-band-yellow">'
        '<span>25 – 50 m (Far Range)</span>'
        '<span><strong>25 cm</strong> [Coarse]</span>'
        '</div>'
        '<div class="grid-res-row res-band-red">'
        '<span>50 – 100 m (Perimeter)</span>'
        '<span><strong>50 cm</strong> [Base]</span>'
        '</div>'
        '<div style="font-size: 0.68rem; color: #64748b; margin-top: 0.35rem; line-height: 1.35;">'
        '<strong style="color: #94a3b8;">High Importance / Dynamic:</strong> Fine 5cm detail<br>'
        '<strong style="color: #94a3b8;">Low Importance / Static:</strong> Coarse 50cm detail'
        '</div>',
        unsafe_allow_html=True,
    )


def render_right_column_panels(
    perception_data: Dict[str, Any],
    is_simulation: bool = True,
) -> None:
    """
    Render the combined right-column stack for the executive dashboard.
    """
    render_semantic_legend_widget()
    render_semantic_distribution_widget(perception_data=perception_data)
    render_adaptive_grid_resolution_widget()
