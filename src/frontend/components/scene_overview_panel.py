"""
Scene Overview & Perception Workflow Pipeline Panel.

Recreates the left vertical pipeline stages from the reference image:
1. Scene Overview: Raw LiDAR Point Cloud (3D) thumbnail
2. AI Semantic Segmentation: Terrain classification, Semantic labels, Confidence
3. Adaptive Grid + 2.5D Mapping: Variable resolution, Elevation map, Semantic layers
"""

from typing import Any, Dict
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.styles import get_dark_plotly_template


def create_pointcloud_thumbnail(perception_data: Dict[str, Any]) -> go.Figure:
    """
    Construct a compact, responsive 3D thumbnail of the raw point cloud.
    """
    fig = go.Figure()
    pts = np.asarray(perception_data.get("points", []), dtype=np.float32)

    if len(pts) > 0:
        sample_step = max(1, len(pts) // 600)
        thumb_pts = pts[::sample_step]

        x = thumb_pts[:, 0]
        y = thumb_pts[:, 1]
        z = thumb_pts[:, 2]

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="markers",
                marker=dict(
                    size=1.8,
                    color=z,
                    colorscale="Turbo",
                    opacity=0.88,
                ),
                hoverinfo="skip",
            )
        )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        scene=dict(
            camera=dict(
                eye=dict(x=-0.2, y=-1.8, z=1.0),
                center=dict(x=0.0, y=0.2, z=0.0),
            ),
            xaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
            yaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
            zaxis=dict(showbackground=False, showticklabels=False, title="", showgrid=False),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=140,
    )
    return fig


def render_scene_overview_panel(perception_data: Dict[str, Any]) -> None:
    """
    Render left vertical workflow cards explaining the perception system architecture.
    """
    # Stage 1 Card: Header
    st.markdown(
        '<div class="pipeline-card active">'
        '<div class="pipeline-header">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2">'
        '<circle cx="12" cy="12" r="10"></circle>'
        '<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>'
        '</svg>'
        '<span>Scene Overview</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 3D Thumbnail inside Stage 1
    fig_thumb = create_pointcloud_thumbnail(perception_data)
    st.plotly_chart(fig_thumb, use_container_width=True, config={"displayModeBar": False})

    # Stage 1 Footer & Connector
    st.markdown(
        '<div style="font-size: 0.70rem; color: #94a3b8; text-align: center; margin-top: -0.25rem;">'
        'Raw LiDAR Point Cloud (3D)'
        '</div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>',
        unsafe_allow_html=True,
    )

    # Stage 2: AI Semantic Segmentation Card
    st.markdown(
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">'
        '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>'
        '</svg>'
        '<span>AI Semantic Segmentation</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Terrain classification</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Semantic labels (8 classes)</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Confidence estimation</div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>',
        unsafe_allow_html=True,
    )

    # Stage 3: Adaptive Grid + 2.5D Mapping Card
    st.markdown(
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">'
        '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>'
        '<line x1="3" y1="9" x2="21" y2="9"></line>'
        '<line x1="9" y1="21" x2="9" y2="9"></line>'
        '</svg>'
        '<span>Adaptive Grid + 2.5D Mapping</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Variable resolution (5-50cm)</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Elevation representation</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Dynamic object subdivision</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Importance refinement</div>'
        '</div>',
        unsafe_allow_html=True,
    )
