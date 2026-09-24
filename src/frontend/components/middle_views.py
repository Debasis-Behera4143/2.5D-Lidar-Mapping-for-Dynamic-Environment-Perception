"""
Middle Sub-Viewport Perception Panels.

Implements Row 2 components from the reference image:
1. 2.5D Elevation Map (Side/Front View) with height colorbar (0.0 to 5.0m)
2. Semantic Map (Top View) with BEV semantic regions and mini legend
"""

from typing import Any, Dict
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.config import DISPLAY_CLASS_COLORS
from src.frontend.styles import get_dark_plotly_template


def create_side_elevation_figure(perception_data: Dict[str, Any]) -> go.Figure:
    """
    Construct side/front elevation cross-section showing road, walls, vehicles,
    and trees with a Turbo height scale (0.0 - 5.0 m).
    """
    fig = go.Figure()
    pts = np.asarray(perception_data.get("points", []), dtype=np.float32)

    if len(pts) > 0:
        step = max(1, len(pts) // 1800)
        view_pts = pts[::step]

        x = view_pts[:, 0]
        y = view_pts[:, 1]
        z = view_pts[:, 2]

        fig.add_trace(
            go.Scatter(
                x=y,
                y=z,
                mode="markers",
                marker=dict(
                    size=4.0,
                    color=z,
                    colorscale="Turbo",
                    cmin=0.0,
                    cmax=5.0,
                    opacity=0.88,
                    colorbar=dict(
                        title=dict(text="Height (m)", font=dict(color="#ffffff", size=10)),
                        thickness=10,
                        len=0.85,
                        tickfont=dict(color="#94a3b8", size=9),
                        x=1.02,
                    ),
                ),
                text=[f"Y: {py:.2f} m<br>Height Z: {pz:.2f} m" for py, pz in zip(y, z)],
                hoverinfo="text",
                showlegend=False,
            )
        )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        xaxis=dict(
            title=dict(text="Lateral Cross-Section Y (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[-10.0, 14.0],
        ),
        yaxis=dict(
            title=dict(text="Height Z (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[-0.2, 5.8],
        ),
        margin=dict(l=35, r=55, t=10, b=30),
        height=230,
    )
    return fig


def create_semantic_top_figure(perception_data: Dict[str, Any]) -> go.Figure:
    """
    Construct 2D Bird's-Eye View (BEV) map with distinct semantic regions.
    """
    fig = go.Figure()
    pts = np.asarray(perception_data.get("points", []), dtype=np.float32)
    labels = np.asarray(perception_data.get("predicted_labels", []), dtype=np.int64)

    if len(pts) > 0 and len(labels) == len(pts):
        step = max(1, len(pts) // 2000)
        view_pts = pts[::step]
        view_lbls = labels[::step]

        x = view_pts[:, 0]
        y = view_pts[:, 1]
        colors = [DISPLAY_CLASS_COLORS.get(int(lbl), "#64748b") for lbl in view_lbls]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker=dict(
                    size=4.5,
                    color=colors,
                    symbol="square",
                    opacity=0.88,
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[0],
                y=[0],
                mode="markers",
                marker=dict(size=9, color="#ffffff", symbol="cross", line=dict(color="#00d4ff", width=2)),
                name="Ego Vehicle",
                showlegend=False,
                hovertext="Ego Vehicle (0, 0)",
                hoverinfo="text",
            )
        )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        xaxis=dict(
            title=dict(text="Forward X (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[-10.0, 55.0],
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            title=dict(text="Lateral Y (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[-10.0, 14.0],
        ),
        margin=dict(l=35, r=15, t=10, b=30),
        height=230,
    )
    return fig


def render_middle_subviews(perception_data: Dict[str, Any]) -> None:
    """
    Render Row 2: 2.5D Elevation Map (Side/Front View) and Semantic Map (Top View).
    """
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            '<div class="viewer-header">'
            '<div class="viewer-title">2.5D Elevation Map (Side/Front View)</div>'
            '<span class="viewer-tag" style="color: #38bdf8;">Height Extrusion</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        fig_side = create_side_elevation_figure(perception_data)
        st.plotly_chart(fig_side, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown(
            '<div class="viewer-header">'
            '<div class="viewer-title">Semantic Map (Top View)</div>'
            '<div style="display: flex; gap: 0.35rem; font-size: 0.68rem; color: #94a3b8;">'
            '<span style="color: #3b82f6;">■ Road</span> '
            '<span style="color: #8b5cf6;">■ Sidewalk</span> '
            '<span style="color: #ef4444;">■ Wall</span> '
            '<span style="color: #10b981;">■ Veg</span> '
            '<span style="color: #d946ef;">■ Vehicle</span>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        fig_top = create_semantic_top_figure(perception_data)
        st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})
