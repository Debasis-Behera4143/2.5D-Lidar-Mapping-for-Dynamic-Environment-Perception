"""
Semantic Perception & Taxonomy Analysis View.

Displays:
- Canonical 8-class project taxonomy with matching hex palettes
- Point distribution per semantic category
- Softmax prediction confidence distribution
- Synchronized Ground Truth evaluation metrics (accuracy, IoU) when authentic labels exist
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.config import CANONICAL_TAXONOMY, CLASS_COLORS, CLASS_NAMES
from src.frontend.styles import get_dark_plotly_template


def render_semantic_legend_panel(
    class_distribution: Optional[Dict[str, int]] = None,
    total_points: int = 0,
) -> None:
    """
    Render compact technical semantic legend panel with live point counts.
    """
    st.markdown('<div class="viewer-title" style="margin-bottom: 0.6rem;">Semantic Legend (8 Classes)</div>', unsafe_allow_html=True)

    dist = class_distribution or {}
    total = max(1, total_points)

    for item in CANONICAL_TAXONOMY:
        c_id = item["id"]
        c_name = item["name"]
        color = item["color"]
        priority = item["priority"]
        count = dist.get(c_name, 0)
        pct = (count / total) * 100.0 if total > 0 and count > 0 else 0.0

        count_str = f"{count:,d} ({pct:.1f}%)" if count > 0 else "0 (0.0%)"

        html_row = f"""
        <div class="legend-row">
            <div style="display: flex; align-items: center;">
                <span class="legend-color-box" style="background-color: {color};"></span>
                <span style="font-weight: 600; color: #ffffff;">{c_name.capitalize()}</span>
                <span style="font-size: 0.68rem; color: #64748b; margin-left: 0.4rem;">[{priority}]</span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: #cbd5e1;">
                {count_str}
            </div>
        </div>
        """
        st.markdown(html_row, unsafe_allow_html=True)


def render_semantic_distribution_chart(
    class_distribution: Dict[str, int],
    total_points: int,
) -> None:
    """
    Render a horizontal bar chart displaying class frequency.
    """
    if not class_distribution:
        st.info("No semantic distribution available.")
        return

    names = []
    counts = []
    colors = []

    for item in reversed(CANONICAL_TAXONOMY):
        c_name = item["name"]
        cnt = class_distribution.get(c_name, 0)
        names.append(c_name.capitalize())
        counts.append(cnt)
        colors.append(item["color"])

    fig = go.Figure(
        go.Bar(
            x=counts,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#1c2b45", width=1)),
            text=[f"{c:,d}" if c > 0 else "" for c in counts],
            textposition="auto",
            textfont=dict(color="#ffffff", size=10),
        )
    )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        xaxis=dict(title="Point Count", zeroline=False),
        yaxis=dict(title=""),
        margin=dict(l=10, r=15, t=10, b=25),
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_semantic_view(
    perception_dict: Dict[str, Any],
    taxonomy_items: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Complete Semantic View Page component.
    """
    st.markdown("### Semantic Perception & 8-Class Taxonomy")
    st.markdown(
        "Quantitative distribution of LiDAR points across canonical functional classes "
        "and corresponding confidence metrics produced by the perception model."
    )

    if not perception_dict:
        st.warning("No LiDAR perception data loaded. Run inference on a sample frame to inspect.")
        return

    total_pts = perception_dict.get("total_points", 0)
    class_dist = perception_dict.get("class_distribution", {})
    conf_info = perception_dict.get("confidence_information", {})
    eval_info = perception_dict.get("evaluation_information")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Class Point Distribution")
        render_semantic_distribution_chart(class_dist, total_pts)

    with col2:
        st.markdown("#### Canonical 8-Class Taxonomy Specifications")
        render_semantic_legend_panel(class_dist, total_pts)

    st.markdown("---")
    st.markdown("#### Perception Confidence Statistics")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        mean_c = conf_info.get("mean")
        v = f"{mean_c * 100:.1f}%" if mean_c is not None else "N/A"
        st.metric("Mean Confidence", v)
    with c2:
        min_c = conf_info.get("min")
        v = f"{min_c * 100:.1f}%" if min_c is not None else "N/A"
        st.metric("Min Confidence", v)
    with c3:
        max_c = conf_info.get("max")
        v = f"{max_c * 100:.1f}%" if max_c is not None else "N/A"
        st.metric("Max Confidence", v)
    with c4:
        std_c = conf_info.get("std")
        v = f"{std_c:.3f}" if std_c is not None else "N/A"
        st.metric("Confidence StdDev", v)

    if eval_info:
        st.markdown("---")
        st.markdown("#### Ground-Truth Synchronized Evaluation")
        e1, e2 = st.columns(2)
        with e1:
            st.metric("Classification Accuracy", f"{eval_info.get('accuracy_percent', 0):.2f}%")
        with e2:
            st.metric("Evaluated Points", f"{eval_info.get('evaluated_points', 0):,d}")
