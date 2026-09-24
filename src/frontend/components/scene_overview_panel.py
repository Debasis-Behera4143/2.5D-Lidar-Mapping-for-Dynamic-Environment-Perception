"""
Perception & Mapping Pipeline Panel (Left Column).

Visualizes the core research workflow with real status indicators:
1. Raw LiDAR Scan (Ingestion & preprocessing)
2. Semantic Segmentation (Point-wise 8-class prediction)
3. Importance & Dynamic Weighting (Multi-criteria trigger)
4. Adaptive Variable Resolution Grid (Recursive quadtree)
5. 2.5D Elevation Surface (Height & occupancy aggregation)
"""

from typing import Any, Dict
import numpy as np
import streamlit as st


def render_scene_overview_panel(perception_data: Dict[str, Any]) -> None:
    """
    Render left vertical pipeline panel explaining the perception system architecture.
    """
    pts = perception_data.get("points", [])
    pts_cnt = len(pts)
    frame_id = perception_data.get("frame_id", "1248")

    st.markdown(
        '<div class="viewer-header">'
        '<div class="viewer-title">Perception Pipeline</div>'
        '<span class="viewer-tag" style="color: #38bdf8;">5 STAGES</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Stage 1: Raw LiDAR Scan
    stage1_html = (
        '<div class="pipeline-card active">'
        '<div class="pipeline-header">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2">'
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="12" y1="8" x2="12" y2="12"></line>'
        '<line x1="12" y1="16" x2="12.01" y2="16"></line>'
        '</svg>'
        '<span>1. Raw LiDAR Scan</span>'
        '</div>'
        f'<div class="pipeline-feature"><span class="check">✓</span> Frame ID: <strong>{frame_id}</strong></div>'
        f'<div class="pipeline-feature"><span class="check">✓</span> Points: <strong>{pts_cnt:,d}</strong></div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Range: <strong>[2.0m, 50.0m]</strong></div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>'
    )
    st.markdown(stage1_html, unsafe_allow_html=True)

    # Stage 2: AI Semantic Segmentation
    stage2_html = (
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">'
        '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>'
        '</svg>'
        '<span>2. Semantic Segmentation</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> 8-Class Project Taxonomy</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Point-wise Softmax</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Confidence Estimation</div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>'
    )
    st.markdown(stage2_html, unsafe_allow_html=True)

    # Stage 3: Importance & Dynamics
    stage3_html = (
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2">'
        '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>'
        '</svg>'
        '<span>3. Importance Weighting</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Semantic Vulnerability</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Dynamic Displacement</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Prediction Uncertainty</div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>'
    )
    st.markdown(stage3_html, unsafe_allow_html=True)

    # Stage 4: Adaptive Quadtree Grid
    stage4_html = (
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">'
        '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>'
        '<line x1="3" y1="9" x2="21" y2="9"></line>'
        '<line x1="9" y1="21" x2="9" y2="9"></line>'
        '</svg>'
        '<span>4. Adaptive Quadtree</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Variable Cell Sizes</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Fine: <strong>0.05m</strong> (Obstacles)</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Coarse: <strong>0.50m</strong> (Background)</div>'
        '</div>'
        '<div class="pipeline-arrow">↓</div>'
    )
    st.markdown(stage4_html, unsafe_allow_html=True)

    # Stage 5: 2.5D Elevation Surface
    stage5_html = (
        '<div class="pipeline-card">'
        '<div class="pipeline-header">'
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">'
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>'
        '</svg>'
        '<span>5. 2.5D Elevation Surface</span>'
        '</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Height Distribution Z(x,y)</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Drivability Mapping</div>'
        '<div class="pipeline-feature"><span class="check">✓</span> Real-Time Representation</div>'
        '</div>'
    )
    st.markdown(stage5_html, unsafe_allow_html=True)
