"""
Frontend styling and CSS injection module.

Implements a professional dark LiDAR workstation theme matching the reference screenshot:
- Deep navy / near-black background (#050913, #09101f, #0d172a)
- Restrained cyan and electric blue technical accents
- High information density, compact layout
- Custom badge pills, metric cards, status indicators, and Plotly templates
- Floating 3D spatial callout annotations
- Multi-stage pipeline workflow cards
- Circular KPI ring gauges (mIoU, FPS, Latency, Memory)
- Engineering terminal logs & footer status strip
"""

import plotly.graph_objects as go
import streamlit as st

CUSTOM_CSS = """
<style>
    /* Dark Engineering Workstation Theme */
    :root {
        --bg-primary: #050913;
        --bg-secondary: #09101f;
        --bg-card: #0d172a;
        --bg-card-hover: #122038;
        --border-subtle: #172742;
        --border-focus: #00d4ff;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-cyan: #00d4ff;
        --accent-blue: #2563eb;
        --accent-green: #10b981;
        --accent-purple: #8b5cf6;
        --accent-magenta: #d946ef;
        --accent-yellow: #eab308;
        --accent-orange: #f97316;
        --accent-red: #ef4444;
    }

    /* Main Container Styles */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Reduce default Streamlit padding for high-density workstation */
    .block-container {
        padding-top: 1.0rem !important;
        padding-bottom: 2.0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Streamlit Header & Toolbar */
    header[data-testid="stHeader"] {
        background: rgba(5, 9, 19, 0.92);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid var(--border-subtle);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"] div.block-container {
        padding-top: 1.25rem !important;
    }

    /* Top Workstation Header */
    .workstation-header {
        background: linear-gradient(90deg, #091224 0%, #0d1b34 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 0.85rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
    }
    .header-title-block {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }
    .header-logo-box {
        width: 42px;
        height: 42px;
        border-radius: 8px;
        background: rgba(0, 212, 255, 0.08);
        border: 1px solid rgba(0, 212, 255, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--accent-cyan);
    }
    .header-title-block h1 {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0;
        color: #ffffff;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 0.76rem;
        color: var(--accent-cyan);
        letter-spacing: 0.04em;
        font-weight: 500;
        margin-top: 0.15rem;
    }
    .header-badges {
        display: flex;
        gap: 0.55rem;
        align-items: center;
    }

    /* Status Pill Badges */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .status-pill.realtime {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border-color: rgba(16, 185, 129, 0.4);
    }
    .status-pill.sim-badge {
        background: rgba(0, 212, 255, 0.12);
        color: #38bdf8;
        border-color: rgba(0, 212, 255, 0.35);
    }
    .status-pill.meta {
        background: rgba(15, 23, 42, 0.8);
        color: #cbd5e1;
        border-color: var(--border-subtle);
    }

    /* Pipeline Workflow Cards (Left Panel) */
    .pipeline-container {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
    }
    .pipeline-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 0.85rem;
        transition: all 0.2s ease;
    }
    .pipeline-card:hover {
        border-color: rgba(0, 212, 255, 0.35);
    }
    .pipeline-card.active {
        border-color: rgba(0, 212, 255, 0.5);
        background: linear-gradient(180deg, #0e1a30 0%, #0d172a 100%);
    }
    .pipeline-header {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.82rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.45rem;
    }
    .pipeline-feature {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.72rem;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .pipeline-feature span.check {
        color: #10b981;
        font-weight: 700;
        font-size: 0.75rem;
    }
    .pipeline-arrow {
        text-align: center;
        color: var(--accent-cyan);
        font-size: 1.05rem;
        line-height: 1;
        margin: -0.1rem 0;
        opacity: 0.8;
    }

    /* Visualizer Panels & Boxes */
    .viewer-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.85rem;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .viewer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.45rem;
        margin-bottom: 0.45rem;
        border-bottom: 1px solid rgba(23, 39, 66, 0.7);
    }
    .viewer-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .viewer-tag {
        font-size: 0.65rem;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        background: rgba(0, 212, 255, 0.1);
        color: var(--accent-cyan);
        border: 1px solid rgba(0, 212, 255, 0.25);
        font-weight: 600;
        text-transform: uppercase;
    }

    /* Semantic Legend Rows */
    .legend-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.28rem 0.55rem;
        background: rgba(10, 17, 31, 0.6);
        border: 1px solid rgba(23, 39, 66, 0.6);
        border-radius: 5px;
        margin-bottom: 0.25rem;
        font-size: 0.75rem;
    }
    .legend-color-box {
        width: 11px;
        height: 11px;
        border-radius: 3px;
        display: inline-block;
        margin-right: 0.45rem;
        flex-shrink: 0;
    }

    /* Object Detection Table */
    .object-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.35rem 0.65rem;
        background: rgba(10, 17, 31, 0.6);
        border: 1px solid rgba(23, 39, 66, 0.6);
        border-radius: 5px;
        margin-bottom: 0.3rem;
        font-size: 0.76rem;
    }
    .object-count-badge {
        font-family: "JetBrains Mono", Consolas, monospace;
        font-weight: 700;
        color: #ffffff;
        background: rgba(30, 41, 59, 0.8);
        padding: 0.1rem 0.5rem;
        border-radius: 4px;
        border: 1px solid #334155;
    }

    /* Adaptive Grid Resolution Pills */
    .grid-res-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.35rem 0.65rem;
        border-radius: 6px;
        margin-bottom: 0.35rem;
        font-size: 0.76rem;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .res-band-blue {
        background: rgba(37, 99, 235, 0.15);
        color: #93c5fd;
        border-color: rgba(37, 99, 235, 0.4);
    }
    .res-band-purple {
        background: rgba(139, 92, 246, 0.15);
        color: #c4b5fd;
        border-color: rgba(139, 92, 246, 0.4);
    }
    .res-band-yellow {
        background: rgba(234, 179, 8, 0.15);
        color: #fde047;
        border-color: rgba(234, 179, 8, 0.4);
    }
    .res-band-red {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border-color: rgba(239, 68, 68, 0.4);
    }

    /* High Density Metric Cards & Circular Gauges */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 0.85rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }
    .metric-card .label {
        font-size: 0.70rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        font-weight: 600;
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
    }
    .metric-badge {
        font-size: 0.58rem;
        padding: 0.1rem 0.35rem;
        border-radius: 3px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-simulation {
        background: rgba(0, 212, 255, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(0, 212, 255, 0.3);
    }
    .badge-measured {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* Terminal System Logs */
    .terminal-log-box {
        background: #03060c;
        border: 1px solid #142238;
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 0.72rem;
        color: #94a3b8;
        max-height: 140px;
        overflow-y: auto;
        line-height: 1.55;
    }
    .terminal-log-line {
        display: flex;
        gap: 0.55rem;
        white-space: nowrap;
    }
    .log-time { color: var(--accent-cyan); }
    .log-msg { color: #e2e8f0; }
    .log-tag-info { color: #60a5fa; }
    .log-tag-success { color: #34d399; font-weight: 600; }
    .log-tag-ready { color: #a78bfa; font-weight: 700; }

    /* Summary Bar at Bottom */
    .summary-footer {
        background: #080f1e;
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.65rem 1.0rem;
        margin-top: 0.85rem;
        display: flex;
        flex-wrap: wrap;
        gap: 1.25rem;
        font-size: 0.75rem;
        color: var(--text-secondary);
        align-items: center;
        justify-content: space-between;
    }
    .summary-left {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        color: #e2e8f0;
    }
    .summary-left strong {
        color: #ffffff;
        font-size: 0.78rem;
    }
    .summary-right {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1.0rem;
    }
    .summary-item {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.74rem;
        color: #94a3b8;
    }
    .summary-item strong {
        color: #ffffff;
    }

    /* Spatial Callout Annotation Overlay */
    .callout-overlay {
        position: relative;
        width: 100%;
        margin-top: -38px;
        display: flex;
        justify-content: space-around;
        padding: 0 10px;
        pointer-events: none;
        z-index: 10;
    }
    .callout-pill {
        background: rgba(9, 16, 31, 0.88);
        backdrop-filter: blur(6px);
        padding: 0.35rem 0.75rem;
        border-radius: 6px;
        font-size: 0.72rem;
        pointer-events: auto;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
        border: 1px solid transparent;
    }
    .callout-pill .title {
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .callout-pill .height {
        color: #94a3b8;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.68rem;
    }
</style>
"""


def apply_custom_styles() -> None:
    """Inject workstation CSS rules into Streamlit DOM."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_dark_plotly_template() -> go.layout.Template:
    """
    Returns unified Plotly dark engineering template matching the workstation.
    """
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="#09101f",
        plot_bgcolor="#09101f",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            size=11,
            color="#94a3b8",
        ),
        title=dict(
            font=dict(color="#ffffff", size=12),
            x=0.02,
            y=0.96,
        ),
        xaxis=dict(
            gridcolor="#15243c",
            linecolor="#1c2d4a",
            tickcolor="#1c2d4a",
            zerolinecolor="#1f3354",
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="#15243c",
            linecolor="#1c2d4a",
            tickcolor="#1c2d4a",
            zerolinecolor="#1f3354",
            showgrid=True,
        ),
        scene=dict(
            xaxis=dict(
                backgroundcolor="#050913",
                gridcolor="#172742",
                linecolor="#1f3354",
                showbackground=True,
                zerolinecolor="#00d4ff",
                title=dict(text="X: Forward (m)", font=dict(color="#00d4ff", size=10)),
            ),
            yaxis=dict(
                backgroundcolor="#050913",
                gridcolor="#172742",
                linecolor="#1f3354",
                showbackground=True,
                zerolinecolor="#ef4444",
                title=dict(text="Y: Lateral (m)", font=dict(color="#ef4444", size=10)),
            ),
            zaxis=dict(
                backgroundcolor="#050913",
                gridcolor="#172742",
                linecolor="#1f3354",
                showbackground=True,
                zerolinecolor="#10b981",
                title=dict(text="Z (Height)", font=dict(color="#10b981", size=10)),
            ),
        ),
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return template
