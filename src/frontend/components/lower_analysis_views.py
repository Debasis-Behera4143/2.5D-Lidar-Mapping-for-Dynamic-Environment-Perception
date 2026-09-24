"""
Lower Analysis & Performance Views Component.

Implements Row 3 from the reference image:
1. Elevation Profile (Front View) with distance vs height gradient contour
2. Performance Metrics: 4 circular SVG ring gauges (mIoU, FPS, Latency, Memory)
3. System Logs: Terminal-style event log with timestamps and status tags
4. Grid Comparison: Side-by-side Uniform (5cm) vs Adaptive Grid (multi-res)
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.styles import get_dark_plotly_template


def create_elevation_profile_chart(profile_data: Dict[str, Any]) -> go.Figure:
    """
    Construct continuous 1D elevation profile area curve matching reference screenshot:
    Distance (0-100m) on X-axis, Height (0-10m) on Y-axis.
    """
    x = profile_data.get("distance_m", list(np.linspace(0, 100, 100)))
    y = profile_data.get("height_m", [0.0] * len(x))

    fig = go.Figure()

    # Fill area with smooth elevation line
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color="#ef4444", width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.28)",
            name="Elevation",
            hovertext=[f"Dist: {dx:.1f} m<br>Height: {dy:.2f} m" for dx, dy in zip(x, y)],
            hoverinfo="text",
        )
    )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        xaxis=dict(
            title=dict(text="Distance (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[0.0, 100.0],
            dtick=20,
        ),
        yaxis=dict(
            title=dict(text="Height (m)", font=dict(color="#94a3b8", size=10)),
            zeroline=True,
            zerolinecolor="#1e2d48",
            range=[0.0, 10.0],
            dtick=5,
        ),
        margin=dict(l=30, r=15, t=10, b=28),
        height=175,
        showlegend=False,
    )
    return fig


def render_circular_kpis(metrics: Dict[str, Any]) -> None:
    """
    Render 4 circular ring gauges matching reference screenshot:
    - mIoU (Semantic Seg.): 87% (green ring)
    - FPS: 18 (blue ring)
    - Latency: 55 ms (purple ring)
    - Memory Usage: 820 MB (orange ring)
    """
    kpis = [
        {
            "label": "mIoU (Semantic Seg.)",
            "val": f"{int(metrics.get('miou_percent', 87))}%",
            "pct": metrics.get("miou_percent", 87.0),
            "color": "#10b981",
            "badge": metrics.get("miou_badge", "SIMULATION"),
        },
        {
            "label": "FPS",
            "val": f"{int(metrics.get('fps', 18))}",
            "pct": min(100.0, metrics.get("fps", 18.0) * 4.0),
            "color": "#38bdf8",
            "badge": metrics.get("fps_badge", "SIMULATION"),
        },
        {
            "label": "Latency",
            "val": f"{int(metrics.get('latency_ms', 55))} ms",
            "pct": min(100.0, metrics.get("latency_ms", 55.0) * 1.2),
            "color": "#a855f7",
            "badge": metrics.get("latency_badge", "SIMULATION"),
        },
        {
            "label": "Memory Usage",
            "val": f"{int(metrics.get('memory_mb', 820))} MB",
            "pct": min(100.0, (metrics.get("memory_mb", 820.0) / 1024.0) * 100.0),
            "color": "#f97316",
            "badge": metrics.get("memory_badge", "SIMULATION"),
        },
    ]

    cols = st.columns(4)
    circumference = 188.5  # 2 * pi * 30

    for col, kpi in zip(cols, kpis):
        with col:
            pct = kpi["pct"]
            offset = circumference * (1.0 - max(0.0, min(1.0, pct / 100.0)))
            b_class = "badge-simulation" if kpi["badge"] == "SIMULATION" else "badge-measured"

            card_html = (
                '<div class="metric-card" style="padding: 0.5rem 0.4rem;">'
                f'<div class="label" style="font-size: 0.65rem;"><span>{kpi["label"]}</span></div>'
                '<div style="position: relative; width: 68px; height: 68px; margin: 0.25rem 0;">'
                '<svg width="68" height="68" viewBox="0 0 68 68" style="transform: rotate(-90deg);">'
                '<circle cx="34" cy="34" r="30" stroke="#132238" stroke-width="6" fill="none"></circle>'
                f'<circle cx="34" cy="34" r="30" stroke="{kpi["color"]}" stroke-width="6" fill="none" '
                f'stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" stroke-linecap="round"></circle>'
                '</svg>'
                '<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; '
                'display: flex; align-items: center; justify-content: center; '
                f'font-family: \'JetBrains Mono\', monospace; font-size: 0.95rem; font-weight: 700; color: #ffffff;">{kpi["val"]}</div>'
                '</div>'
                f'<span class="metric-badge {b_class}">{kpi["badge"]}</span>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)


def render_system_logs_widget(logs: List[Dict[str, str]]) -> None:
    """
    Render terminal log box with color-coded timestamps and tags.
    """
    lines_html = []
    for item in logs:
        t = item.get("time", "00:00:00")
        tag = item.get("tag", "INFO")
        msg = item.get("msg", "")

        tag_cls = "log-tag-info"
        if tag == "SUCCESS":
            tag_cls = "log-tag-success"
        elif tag == "READY":
            tag_cls = "log-tag-ready"

        lines_html.append(
            f'<div class="terminal-log-line">'
            f'<span class="log-time">{t}</span> '
            f'<span class="{tag_cls}">[{tag}]</span> '
            f'<span class="log-msg">{msg}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="terminal-log-box">{"".join(lines_html)}</div>',
        unsafe_allow_html=True,
    )


def create_mini_grid_comparison_figures() -> tuple[go.Figure, go.Figure]:
    """
    Create side-by-side mini heatmaps of Uniform Grid vs Adaptive Grid.
    """
    # 1. Uniform Grid (all cells equal size 1.0)
    fig_uni = go.Figure()
    ux = []
    uy = []
    for x in np.arange(-4, 5, 1):
        for y in np.arange(-4, 5, 1):
            ux.append(x)
            uy.append(y)
    fig_uni.add_trace(
        go.Scatter(
            x=ux, y=uy,
            mode="markers",
            marker=dict(size=9, symbol="square", color="rgba(59, 130, 246, 0.8)", line=dict(color="#172742", width=1)),
            hoverinfo="skip",
        )
    )
    template = get_dark_plotly_template()
    fig_uni.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        xaxis=dict(showgrid=False, showticklabels=False, title="", range=[-5, 5]),
        yaxis=dict(showgrid=False, showticklabels=False, title="", range=[-5, 5]),
        margin=dict(l=5, r=5, t=5, b=5),
        height=110,
        showlegend=False,
    )

    # 2. Adaptive Grid (fine cells at center, coarser cells at perimeter)
    fig_ada = go.Figure()
    ax = []
    ay = []
    asizes = []
    acolors = []
    # Center fine cells
    for x in np.arange(-2, 2.1, 0.5):
        for y in np.arange(-2, 2.1, 0.5):
            ax.append(x)
            ay.append(y)
            asizes.append(5)
            acolors.append("rgba(0, 212, 255, 0.9)")
    # Perimeter coarse cells
    for x in [-4, 4]:
        for y in np.arange(-4, 5, 2):
            ax.append(x)
            ay.append(y)
            asizes.append(14)
            acolors.append("rgba(249, 115, 22, 0.75)")
    for y in [-4, 4]:
        for x in [-2, 0, 2]:
            ax.append(x)
            ay.append(y)
            asizes.append(14)
            acolors.append("rgba(249, 115, 22, 0.75)")

    fig_ada.add_trace(
        go.Scatter(
            x=ax, y=ay,
            mode="markers",
            marker=dict(size=asizes, symbol="square", color=acolors, line=dict(color="#172742", width=1)),
            hoverinfo="skip",
        )
    )
    fig_ada.update_layout(
        template=template,
        paper_bgcolor="#0d172a",
        plot_bgcolor="#0d172a",
        xaxis=dict(showgrid=False, showticklabels=False, title="", range=[-5, 5]),
        yaxis=dict(showgrid=False, showticklabels=False, title="", range=[-5, 5]),
        margin=dict(l=5, r=5, t=5, b=5),
        height=110,
        showlegend=False,
    )

    return fig_uni, fig_ada


def render_lower_analysis_views(
    elevation_profile: Dict[str, Any],
    performance_metrics: Dict[str, Any],
    system_logs: List[Dict[str, str]],
    comparison_data: Dict[str, Any],
) -> None:
    """
    Render Row 3: Elevation Profile, Performance & Logs, Grid Comparison.
    """
    col_elev, col_perf_logs, col_grid_comp = st.columns([3, 5, 4])

    with col_elev:
        st.markdown(
            '<div class="viewer-header">'
            '<div class="viewer-title">Elevation Profile (Front View)</div>'
            '<span class="viewer-tag" style="color: #ef4444;">1D Contour</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        fig_prof = create_elevation_profile_chart(elevation_profile)
        st.plotly_chart(fig_prof, use_container_width=True, config={"displayModeBar": False})

    with col_perf_logs:
        st.markdown(
            '<div class="viewer-header">'
            '<div class="viewer-title">Performance Metrics & System Logs</div>'
            '<span class="viewer-tag" style="color: #10b981;">Real-Time</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        render_circular_kpis(performance_metrics)
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        render_system_logs_widget(system_logs)

    with col_grid_comp:
        st.markdown(
            '<div class="viewer-header">'
            '<div class="viewer-title">Grid Comparison</div>'
            '<span class="viewer-tag" style="color: #f59e0b;">-68% Cells</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        c_u, c_a = st.columns(2)
        fig_u, fig_a = create_mini_grid_comparison_figures()
        with c_u:
            st.caption("Uniform Grid (5 cm)")
            st.plotly_chart(fig_u, use_container_width=True, config={"displayModeBar": False})
        with c_a:
            st.caption("Adaptive Grid (Multi-res)")
            st.plotly_chart(fig_a, use_container_width=True, config={"displayModeBar": False})

        # Efficiency stats strip
        st.markdown(
            '<div style="display: flex; justify-content: space-around; font-size: 0.72rem; '
            'background: rgba(10, 16, 30, 0.7); border: 1px solid #142238; border-radius: 5px; padding: 0.35rem 0.5rem; margin-top: 0.25rem;">'
            '<div><strong style="color: #38bdf8;">Cells:</strong> 26.4k → 8.4k (-68%)</div>'
            '<div><strong style="color: #34d399;">Memory:</strong> -64%</div>'
            '<div><strong style="color: #a78bfa;">Speedup:</strong> 3.2x</div>'
            '</div>',
            unsafe_allow_html=True,
        )
