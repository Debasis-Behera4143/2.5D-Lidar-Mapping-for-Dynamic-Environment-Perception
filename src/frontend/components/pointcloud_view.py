"""
Interactive 3D LiDAR Point Cloud Visualizer.

Provides high-performance Plotly 3D scatter visualization with:
- Semantic color coding (8-class taxonomy)
- Elevation (Z gradient) color mapping
- LiDAR reflectance intensity mapping
- Ground Truth vs Prediction error maps
- Camera angle presets: 3D Perspective, Top View (BEV), Side View
- 3D bounding boxes for detected objects
- Tooltip hover data (X, Y, Z, semantic label, confidence)
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.config import CLASS_COLORS, CLASS_NAMES
from src.frontend.data_adapter import extract_candidate_clusters, get_preview_points
from src.frontend.styles import get_dark_plotly_template


def create_pointcloud_figure(
    perception_dict: Dict[str, Any],
    color_mode: str = "Semantic",
    view_preset: str = "3D Perspective",
    selected_classes: Optional[List[int]] = None,
    min_confidence: float = 0.0,
    preview_limit: int = 4000,
    show_bboxes: bool = True,
    show_axes: bool = True,
) -> go.Figure:
    """
    Construct an interactive Plotly 3D figure from perception data.
    """
    fig = go.Figure()

    if not perception_dict or "points" not in perception_dict:
        fig.update_layout(
            template=get_dark_plotly_template(),
            annotations=[
                dict(
                    text="No LiDAR scan loaded. Select a frame and click 'Run Perception'.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#64748b"),
                )
            ],
            height=580,
        )
        return fig

    # Filter and downsample for WebGL responsiveness
    pts_data = get_preview_points(
        perception_dict,
        max_points=preview_limit,
        selected_classes=selected_classes,
        min_confidence=min_confidence,
    )

    if not pts_data or pts_data.get("visible_points", 0) == 0:
        fig.update_layout(
            template=get_dark_plotly_template(),
            annotations=[
                dict(
                    text="No points match current class and confidence filter criteria.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#f59e0b"),
                )
            ],
            height=580,
        )
        return fig

    x = pts_data["x"]
    y = pts_data["y"]
    z = pts_data["z"]
    intensity = pts_data["intensity"]
    labels = pts_data["labels"]
    confs = pts_data["confidences"]
    class_names = pts_data["class_names"]

    # Determine point color array
    if color_mode == "Elevation (Z)":
        marker_color = z
        colorscale = "Turbo"
        show_cbar = True
        cbar_title = "Z (m)"
    elif color_mode == "Intensity":
        marker_color = intensity
        colorscale = "Viridis"
        show_cbar = True
        cbar_title = "Intensity"
    elif color_mode == "Error Map" and "ground_truth_labels" in perception_dict:
        gt_raw = np.asarray(perception_dict["ground_truth_labels"])
        # Match slice
        raw_pts = np.asarray(perception_dict["points"])
        is_correct = (labels == gt_raw[:len(labels)])
        marker_color = ["#10b981" if c else "#ef4444" for c in is_correct]
        colorscale = None
        show_cbar = False
        cbar_title = ""
    else:  # Semantic
        marker_color = pts_data["colors"]
        colorscale = None
        show_cbar = False
        cbar_title = ""

    hover_text = [
        f"<b>{cls}</b><br>X: {px:.2f}m<br>Y: {py:.2f}m<br>Z: {pz:.2f}m<br>Conf: {conf * 100:.1f}%<br>Int: {intens:.2f}"
        for px, py, pz, cls, conf, intens in zip(x, y, z, class_names, confs, intensity)
    ]

    # Main Point Cloud Trace
    scatter_kwargs: Dict[str, Any] = dict(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(
            size=2.2,
            color=marker_color,
            opacity=0.88,
        ),
        text=hover_text,
        hoverinfo="text",
        name="LiDAR Points",
    )
    if colorscale and show_cbar:
        scatter_kwargs["marker"]["colorscale"] = colorscale
        scatter_kwargs["marker"]["colorbar"] = dict(
            title=dict(text=cbar_title, font=dict(color="#ffffff", size=10)),
            thickness=12,
            len=0.6,
            tickfont=dict(color="#94a3b8", size=9),
            x=1.02,
        )

    fig.add_trace(go.Scatter3d(**scatter_kwargs))

    # Optional 3D Bounding Boxes around candidate clusters
    if show_bboxes and len(x) > 0:
        raw_pts = np.asarray(perception_dict["points"])
        raw_lbls = np.asarray(perception_dict.get("predicted_labels", []))
        clusters = extract_candidate_clusters(raw_pts, raw_lbls, target_classes=[4, 5, 6])

        for cluster in clusters:
            min_b = cluster["min_bound"]
            max_b = cluster["max_bound"]
            c_name = cluster["class_name"]

            # 12 edges of 3D box
            bx = [min_b[0], max_b[0], max_b[0], min_b[0], min_b[0],
                  min_b[0], max_b[0], max_b[0], min_b[0], min_b[0],
                  None, min_b[0], min_b[0], None, max_b[0], max_b[0],
                  None, max_b[0], max_b[0], None, min_b[0], min_b[0]]
            by = [min_b[1], min_b[1], max_b[1], max_b[1], min_b[1],
                  min_b[1], min_b[1], max_b[1], max_b[1], min_b[1],
                  None, max_b[1], max_b[1], None, max_b[1], max_b[1],
                  None, min_b[1], min_b[1], None, min_b[1], min_b[1]]
            bz = [min_b[2], min_b[2], min_b[2], min_b[2], min_b[2],
                  max_b[2], max_b[2], max_b[2], max_b[2], max_b[2],
                  None, min_b[2], max_b[2], None, min_b[2], max_b[2],
                  None, min_b[2], max_b[2], None, min_b[2], max_b[2]]

            box_color = CLASS_COLORS.get(cluster["class_id"], "#00d4ff")
            fig.add_trace(go.Scatter3d(
                x=bx, y=by, z=bz,
                mode="lines",
                line=dict(color=box_color, width=3),
                name=f"{c_name} Box #{cluster['cluster_id']}",
                hoverinfo="name",
                showlegend=False,
            ))

    # Camera View Presets
    if view_preset == "Top View (BEV)":
        camera = dict(
            eye=dict(x=0.0, y=0.0, z=2.2),
            up=dict(x=1.0, y=0.0, z=0.0),
            center=dict(x=0.0, y=0.0, z=0.0),
        )
    elif view_preset == "Side View":
        camera = dict(
            eye=dict(x=0.0, y=-2.5, z=0.2),
            up=dict(x=0.0, y=0.0, z=1.0),
            center=dict(x=0.0, y=0.0, z=0.0),
        )
    else:  # 3D Perspective
        camera = dict(
            eye=dict(x=-1.6, y=-1.6, z=1.3),
            up=dict(x=0.0, y=0.0, z=1.0),
            center=dict(x=0.0, y=0.0, z=0.0),
        )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        scene=dict(
            camera=camera,
            aspectmode="data",
            xaxis=dict(
                title="X: Forward (m)",
                visible=show_axes,
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
            ),
            yaxis=dict(
                title="Y: Lateral (m)",
                visible=show_axes,
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
            ),
            zaxis=dict(
                title="Z: Elevation (m)",
                visible=show_axes,
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
            ),
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=580,
        showlegend=False,
    )

    return fig


def render_pointcloud_view(
    perception_dict: Dict[str, Any],
    color_mode: str = "Semantic",
    view_preset: str = "3D Perspective",
    selected_classes: Optional[List[int]] = None,
    min_confidence: float = 0.0,
    preview_limit: int = 4000,
    show_bboxes: bool = True,
    show_axes: bool = True,
) -> None:
    """Streamlit wrapper rendering the 3D point cloud viewer."""
    fig = create_pointcloud_figure(
        perception_dict=perception_dict,
        color_mode=color_mode,
        view_preset=view_preset,
        selected_classes=selected_classes,
        min_confidence=min_confidence,
        preview_limit=preview_limit,
        show_bboxes=show_bboxes,
        show_axes=show_axes,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
