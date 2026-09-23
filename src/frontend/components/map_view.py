"""
2.5D Grid Map & Adaptive Variable-Resolution Visualizer.

Renders:
- Adaptive coarse-to-fine cell partitioning (quadtree-style variable resolution)
- 2.5D Elevation Heatmap (Z height per cell)
- Semantic Top-Down (BEV) Grid Map
- Importance Heatmap (multi-criteria subdivision triggers)
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.config import CLASS_COLORS, CLASS_NAMES
from src.frontend.styles import get_dark_plotly_template


def create_2d_grid_figure(
    map_dict: Dict[str, Any],
    color_by: str = "Resolution Level",  # 'Resolution Level', 'Elevation (Height)', 'Semantic Class', 'Importance'
    show_subdivision_boundaries: bool = True,
) -> go.Figure:
    """
    Construct a 2D Bird's-Eye View (BEV) Plotly figure displaying variable-resolution grid cells.
    """
    fig = go.Figure()

    if not map_dict or "cells" not in map_dict or len(map_dict["cells"]) == 0:
        fig.update_layout(
            template=get_dark_plotly_template(),
            annotations=[
                dict(
                    text="No 2.5D Map generated. Click 'Generate 2.5D Maps' to compute.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#64748b"),
                )
            ],
            height=540,
        )
        return fig

    cells = map_dict["cells"]

    cx = [c["center_x"] for c in cells]
    cy = [c["center_y"] for c in cells]
    res = [c.get("resolution", 1.0) for c in cells]
    level = [c.get("level", "fine" if r < 0.5 else "coarse") for c, r in zip(cells, res)]
    mean_h = [c.get("mean_height", 0.0) for c in cells]
    pt_cnt = [c.get("point_count", 0) for c in cells]
    dom_cls = [c.get("dominant_class", 7) for c in cells]
    imp_scores = [c.get("importance_score", 0.0) for c in cells]
    is_dyn = [c.get("is_dynamic", False) for c in cells]

    # Marker sizing and colors
    hover_texts = []
    marker_colors = []
    colorscale = None
    show_cbar = False
    cbar_title = ""

    for i in range(len(cells)):
        c_name = CLASS_NAMES.get(dom_cls[i], f"class_{dom_cls[i]}")
        dyn_str = " (DYNAMIC)" if is_dyn[i] else ""
        hover_texts.append(
            f"<b>Cell #{i}</b>{dyn_str}<br>"
            f"Center: ({cx[i]:.2f}, {cy[i]:.2f})m<br>"
            f"Resolution: {res[i]:.2f}m [{level[i].upper()}]<br>"
            f"Mean Height: {mean_h[i]:.2f}m<br>"
            f"Points: {pt_cnt[i]}<br>"
            f"Dominant: {c_name}<br>"
            f"Importance: {imp_scores[i]:.3f}"
        )

    if color_by == "Resolution Level":
        marker_colors = ["#f59e0b" if l == "fine" else "#3b82f6" for l in level]
    elif color_by == "Elevation (Height)":
        marker_colors = mean_h
        colorscale = "Turbo"
        show_cbar = True
        cbar_title = "Height (m)"
    elif color_by == "Semantic Class":
        marker_colors = [CLASS_COLORS.get(cls, "#a5a5a5") for cls in dom_cls]
    elif color_by == "Importance":
        marker_colors = imp_scores
        colorscale = "Plasma"
        show_cbar = True
        cbar_title = "Importance"

    # Scale marker symbol sizes proportionally to resolution
    # Fine resolution cells render smaller, coarse cells render larger
    marker_sizes = [max(4.0, min(24.0, r * 14.0)) for r in res]

    scatter_kwargs: Dict[str, Any] = dict(
        x=cx,
        y=cy,
        mode="markers",
        marker=dict(
            symbol="square",
            size=marker_sizes,
            color=marker_colors,
            opacity=0.85,
            line=dict(width=1, color="rgba(0, 0, 0, 0.4)") if show_subdivision_boundaries else dict(width=0),
        ),
        text=hover_texts,
        hoverinfo="text",
        name="Grid Cells",
    )

    if colorscale and show_cbar:
        scatter_kwargs["marker"]["colorscale"] = colorscale
        scatter_kwargs["marker"]["colorbar"] = dict(
            title=dict(text=cbar_title, font=dict(color="#ffffff", size=10)),
            thickness=12,
            len=0.7,
            tickfont=dict(color="#94a3b8", size=9),
            x=1.02,
        )

    fig.add_trace(go.Scatter(**scatter_kwargs))

    # Add ego-vehicle center marker at (0, 0)
    fig.add_trace(
        go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(size=10, color="#ffffff", symbol="cross", line=dict(width=2, color="#00d4ff")),
            name="Ego Vehicle",
            hovertext="Ego Vehicle (0, 0)",
            hoverinfo="text",
        )
    )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        xaxis=dict(title="X: Forward Distance (m)", zeroline=True, zerolinecolor="#1e293b", scaleanchor="y", scaleratio=1),
        yaxis=dict(title="Y: Lateral Distance (m)", zeroline=True, zerolinecolor="#1e293b"),
        margin=dict(l=25, r=25, t=25, b=25),
        height=540,
        showlegend=False,
    )

    return fig


def render_map_view(
    map_dict: Dict[str, Any],
    title: str = "Adaptive Variable-Resolution 2.5D Map",
    color_by: str = "Resolution Level",
) -> None:
    """Streamlit component rendering the 2.5D grid map."""
    fig = create_2d_grid_figure(map_dict=map_dict, color_by=color_by)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
