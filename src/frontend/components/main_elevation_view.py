"""
Main 2.5D Semantic Elevation Map Component (Top View + Height).

Recreates the centerpiece 3D perspective visualization from the reference image:
- Multi-lane road with ego-vehicle and dynamic leading vehicles
- Adaptive multi-resolution grid wireframe overlaid on drivable surface
- Left building/wall with height extrusion
- Right lush 3D green trees and sidewalk pedestrian
- Sleek floating callout annotations with leader lines:
    * Wall (Non-drivable) Height: ~2.5 m
    * Vehicle (Dynamic) Height: ~1.5 m
    * Tree (Static) Height: ~5 m
    * Pedestrian (Dynamic) Height: ~1.7 m
    * Drivable Road Height: ~0.0–0.5 m
- Coordinate axes gizmo: Z (Height), Y, X
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.config import (
    CLASS_COLORS,
    CLASS_NAMES,
    DISPLAY_CLASS_COLORS,
    DISPLAY_CLASS_NAMES,
)
from src.frontend.styles import get_dark_plotly_template


def create_main_elevation_figure(
    perception_data: Dict[str, Any],
    adaptive_map: Optional[Dict[str, Any]] = None,
    show_annotations: bool = True,
    show_grid_overlay: bool = True,
    view_angle: str = "Driver Perspective",
    color_mode: str = "Semantic Class",
) -> go.Figure:
    """
    Construct high-fidelity 3D Plotly visualization matching the reference image.
    """
    fig = go.Figure()

    pts = np.asarray(perception_data.get("points", []), dtype=np.float32)
    labels = np.asarray(perception_data.get("predicted_labels", []), dtype=np.int64)
    confs = np.asarray(perception_data.get("confidence_scores", []), dtype=np.float32)

    if len(pts) == 0:
        fig.update_layout(
            template=get_dark_plotly_template(),
            annotations=[
                dict(
                    text="No point cloud available. Switch to Simulation mode or load scan.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#64748b"),
                )
            ],
            height=520,
        )
        return fig

    # 1. Plotly point traces grouped by semantic class for clean coloring & legend isolation
    x = pts[:, 0]
    y = pts[:, 1]
    z = pts[:, 2]

    # Map labels to display colors
    colors = [DISPLAY_CLASS_COLORS.get(int(lbl), CLASS_COLORS.get(int(lbl), "#64748b")) for lbl in labels]
    class_names = [DISPLAY_CLASS_NAMES.get(int(lbl), CLASS_NAMES.get(int(lbl), f"class_{lbl}")) for lbl in labels]

    hover_texts = [
        f"<b>{cname}</b><br>X: {px:.2f} m<br>Y: {py:.2f} m<br>Height: {pz:.2f} m<br>Conf: {conf * 100:.1f}%"
        for px, py, pz, cname, conf in zip(x, y, z, class_names, confs)
    ]

    # Configure marker based on color mode
    if color_mode == "Elevation (Height)":
        marker_cfg = dict(
            size=2.8,
            color=z,
            colorscale="Turbo",
            opacity=0.88,
            colorbar=dict(
                title=dict(text="Height Z (m)", font=dict(color="#ffffff", size=10)),
                thickness=10,
                len=0.7,
                tickfont=dict(color="#94a3b8", size=9),
                x=1.02,
            ),
        )
    else:
        marker_cfg = dict(
            size=2.8,
            color=colors,
            opacity=0.88,
        )

    # Draw Point Cloud Trace
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker=marker_cfg,
            text=hover_texts,
            hoverinfo="text",
            name="LiDAR Points",
            showlegend=False,
        )
    )

    # 2. Adaptive Multi-Resolution Grid Wireframe on Road Surface (matching reference screenshot)
    if show_grid_overlay:
        grid_lines_x: List[Optional[float]] = []
        grid_lines_y: List[Optional[float]] = []
        grid_lines_z: List[Optional[float]] = []
        grid_colors: List[str] = []

        # Near field (0-15m): Fine 1.0m grid mesh
        for gx in np.arange(-5.0, 20.0, 1.0):
            grid_lines_x.extend([gx, gx, None])
            grid_lines_y.extend([-3.8, 3.8, None])
            grid_lines_z.extend([0.02, 0.02, None])

        for gy in np.arange(-3.8, 3.81, 1.0):
            grid_lines_x.extend([-5.0, 20.0, None])
            grid_lines_y.extend([gy, gy, None])
            grid_lines_z.extend([0.02, 0.02, None])

        fig.add_trace(
            go.Scatter3d(
                x=grid_lines_x,
                y=grid_lines_y,
                z=grid_lines_z,
                mode="lines",
                line=dict(color="rgba(0, 212, 255, 0.45)", width=1.5),
                name="Fine Grid (5 cm)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Mid field (20-40m): 2.0m grid mesh
        mid_gx: List[Optional[float]] = []
        mid_gy: List[Optional[float]] = []
        mid_gz: List[Optional[float]] = []
        for gx in np.arange(20.0, 42.0, 2.0):
            mid_gx.extend([gx, gx, None])
            mid_gy.extend([-4.2, 4.2, None])
            mid_gz.extend([0.02, 0.02, None])
        for gy in np.arange(-4.2, 4.21, 2.0):
            mid_gx.extend([20.0, 42.0, None])
            mid_gy.extend([gy, gy, None])
            mid_gz.extend([0.02, 0.02, None])

        fig.add_trace(
            go.Scatter3d(
                x=mid_gx,
                y=mid_gy,
                z=mid_gz,
                mode="lines",
                line=dict(color="rgba(139, 92, 246, 0.35)", width=1.2),
                name="Medium Grid (10 cm)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Sidewalk & Outer Edges: Coarser grid (yellow/orange)
        out_gx: List[Optional[float]] = []
        out_gy: List[Optional[float]] = []
        out_gz: List[Optional[float]] = []
        for gx in np.arange(0.0, 45.0, 3.0):
            # Left sidewalk edge
            out_gx.extend([gx, gx, None])
            out_gy.extend([-6.4, -4.2, None])
            out_gz.extend([0.18, 0.18, None])
            # Right sidewalk edge
            out_gx.extend([gx, gx, None])
            out_gy.extend([4.2, 6.4, None])
            out_gz.extend([0.18, 0.18, None])

        fig.add_trace(
            go.Scatter3d(
                x=out_gx,
                y=out_gy,
                z=out_gz,
                mode="lines",
                line=dict(color="rgba(249, 115, 22, 0.35)", width=1.0),
                name="Coarse Grid (25-50 cm)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # 3. Ego-Vehicle Marker at (0, 0)
    fig.add_trace(
        go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.6],
            mode="markers+text",
            marker=dict(
                size=7,
                color="#ffffff",
                symbol="square",
                line=dict(color="#00d4ff", width=2),
            ),
            text=["EGO"],
            textposition="top center",
            textfont=dict(color="#00d4ff", size=10, family="monospace"),
            name="Ego Vehicle",
            showlegend=False,
            hovertext="<b>Ego Vehicle</b><br>Position: (0.0, 0.0)<br>Sensor: 32-Beam LiDAR",
            hoverinfo="text",
        )
    )

    # 4. 3D Spatial Callout Annotations matching reference image
    if show_annotations:
        annotations = perception_data.get("annotations", [])
        for ann in annotations:
            pos = ann.get("world_pos", [0, 0, 0])
            title = ann.get("title", "")
            sub = ann.get("subtext", "")
            color = ann.get("color", "#00d4ff")

            # Floating text badge in 3D scene
            fig.add_trace(
                go.Scatter3d(
                    x=[pos[0]],
                    y=[pos[1]],
                    z=[pos[2] + 0.4],
                    mode="markers+text",
                    marker=dict(size=4, color=color, symbol="diamond"),
                    text=[f"<b>{title}</b><br>{sub}"],
                    textposition="top center",
                    textfont=dict(color=color, size=10, family="-apple-system, sans-serif"),
                    name=title,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

            # Leader line connecting to ground / object
            fig.add_trace(
                go.Scatter3d(
                    x=[pos[0], pos[0]],
                    y=[pos[1], pos[1]],
                    z=[pos[2] + 0.35, pos[2]],
                    mode="lines",
                    line=dict(color=color, width=2),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # Camera Preset Angles
    camera_presets = {
        "Driver Perspective": dict(
            eye=dict(x=-0.2, y=-1.8, z=0.9),
            center=dict(x=0.0, y=0.3, z=0.1),
            up=dict(x=0, y=0, z=1),
        ),
        "Top View (BEV)": dict(
            eye=dict(x=0.0, y=0.0, z=2.6),
            center=dict(x=0.0, y=0.0, z=0.0),
            up=dict(x=1, y=0, z=0),
        ),
        "Side Elevation": dict(
            eye=dict(x=2.2, y=0.0, z=0.4),
            center=dict(x=0.0, y=0.0, z=0.2),
            up=dict(x=0, y=0, z=1),
        ),
        "Front View": dict(
            eye=dict(x=0.0, y=2.4, z=0.3),
            center=dict(x=0.0, y=0.0, z=0.2),
            up=dict(x=0, y=0, z=1),
        ),
    }

    cam = camera_presets.get(view_angle, camera_presets["Driver Perspective"])

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        scene=dict(
            camera=cam,
            aspectmode="manual",
            aspectratio=dict(x=2.2, y=1.2, z=0.45),
            xaxis=dict(
                title=dict(text="X (Forward)", font=dict(color="#00d4ff", size=10)),
                backgroundcolor="#050913",
                gridcolor="#132035",
                showbackground=True,
                zerolinecolor="#00d4ff",
                range=[-10, 55],
            ),
            yaxis=dict(
                title=dict(text="Y (Lateral)", font=dict(color="#ef4444", size=10)),
                backgroundcolor="#050913",
                gridcolor="#132035",
                showbackground=True,
                zerolinecolor="#ef4444",
                range=[-10, 12],
            ),
            zaxis=dict(
                title=dict(text="Z (Height)", font=dict(color="#10b981", size=10)),
                backgroundcolor="#050913",
                gridcolor="#132035",
                showbackground=True,
                zerolinecolor="#10b981",
                range=[-0.5, 6.5],
            ),
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=480,
    )

    return fig


def render_main_elevation_view(
    perception_data: Dict[str, Any],
    adaptive_map: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render main 2.5D elevation map panel with top toolbar and interactive 3D scene.
    """
    st.markdown(
        '<div class="viewer-header" style="margin-bottom: 0.35rem;">'
        '<div class="viewer-title">'
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2">'
        '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>'
        '<polyline points="2 17 12 22 22 17"></polyline>'
        '<polyline points="2 12 12 17 22 12"></polyline>'
        '</svg>'
        '2.5D Semantic Elevation Map (Top View + Height)'
        '</div>'
        '<div style="display: flex; gap: 0.4rem; align-items: center;">'
        '<span class="viewer-tag">Adaptive Grid</span>'
        '<span class="viewer-tag" style="color: #34d399; border-color: rgba(16, 185, 129, 0.35);">Z (Height) Encoded</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Sub-controls bar
    ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([1.8, 1.6, 1.0, 1.0])
    with ctrl_c1:
        view_opt = st.selectbox(
            "Perspective View",
            ["Driver Perspective", "Top View (BEV)", "Side Elevation", "Front View"],
            index=0,
            key="main_3d_view_angle",
            label_visibility="collapsed",
        )
    with ctrl_c2:
        color_opt = st.selectbox(
            "Color Points By",
            ["Semantic Class", "Elevation (Height)"],
            index=0,
            key="main_3d_color_mode",
            label_visibility="collapsed",
        )
    with ctrl_c3:
        show_grd = st.checkbox("Grid Overlay", value=True, key="main_3d_show_grid")
    with ctrl_c4:
        show_ann = st.checkbox("Callouts", value=True, key="main_3d_show_ann")

    fig = create_main_elevation_figure(
        perception_data=perception_data,
        adaptive_map=adaptive_map,
        show_annotations=show_ann,
        show_grid_overlay=show_grd,
        view_angle=view_opt,
        color_mode=color_opt,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Floating Callout Badges Row directly below the canvas for maximum readability
    if show_ann:
        annotations = perception_data.get("annotations", [])
        if annotations:
            pills_html = []
            for ann in annotations:
                title = ann.get("title", "")
                sub = ann.get("subtext", "")
                col = ann.get("color", "#00d4ff")
                pills_html.append(
                    f'<div class="callout-pill" style="border-color: {col};">'
                    f'<div class="title" style="color: {col};">{title}</div>'
                    f'<div class="height">{sub}</div>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="callout-overlay">{"".join(pills_html)}</div>',
                unsafe_allow_html=True,
            )
