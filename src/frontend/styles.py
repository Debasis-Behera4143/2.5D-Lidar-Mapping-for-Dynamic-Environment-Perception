"""
Frontend styling and CSS injection module.

Implements a professional dark LiDAR workstation theme:
- Deep navy/near-black backgrounds
- Restrained cyan and electric blue accents
- High information density, compact layout
- Custom badge pills, metric cards, status indicators, and Plotly templates
"""

import plotly.graph_objects as go
import streamlit as st

CUSTOM_CSS = """
<style>
    /* Dark Engineering Workstation Theme */
    :root {
        --bg-primary: #070b12;
        --bg-secondary: #0c1322;
        --bg-card: #111a2e;
        --bg-card-hover: #16223a;
        --border-subtle: #1c2b45;
        --border-focus: #00d4ff;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --accent-cyan: #00d4ff;
        --accent-blue: #3b82f6;
        --accent-green: #10b981;
        --accent-amber: #f59e0b;
        --accent-red: #ef4444;
    }

    /* Main Container Styles */
    .stApp {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Streamlit Header & Toolbar */
    header[data-testid="stHeader"] {
        background: rgba(7, 11, 18, 0.85);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid var(--border-subtle);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border-subtle);
    }
    section[data-testid="stSidebar"] div.block-container {
        padding-top: 1.5rem;
    }

    /* Top Workstation Header */
    .workstation-header {
        background: linear-gradient(90deg, #0a1120 0%, #111c30 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .header-title-block h1 {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .header-subtitle {
        font-size: 0.78rem;
        color: var(--accent-cyan);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-top: 0.15rem;
    }
    .header-badges {
        display: flex;
        gap: 0.6rem;
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
        letter-spacing: 0.03em;
        border: 1px solid transparent;
    }
    .status-pill.online {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border-color: rgba(16, 185, 129, 0.3);
    }
    .status-pill.offline {
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border-color: rgba(239, 68, 68, 0.3);
    }
    .status-pill.info {
        background: rgba(59, 130, 246, 0.12);
        color: #60a5fa;
        border-color: rgba(59, 130, 246, 0.3);
    }
    .status-pill.warning {
        background: rgba(245, 158, 11, 0.12);
        color: #fbbf24;
        border-color: rgba(245, 158, 11, 0.3);
    }

    /* High Density Metric Cards */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        position: relative;
        overflow: hidden;
        transition: border-color 0.15s ease;
    }
    .metric-card:hover {
        border-color: rgba(0, 212, 255, 0.4);
    }
    .metric-card .label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .metric-card .value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #ffffff;
        font-family: "JetBrains Mono", Consolas, monospace;
        line-height: 1.2;
    }
    .metric-card .subtext {
        font-size: 0.7rem;
        color: var(--text-secondary);
        margin-top: 0.25rem;
    }
    .metric-badge {
        font-size: 0.62rem;
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
        margin-left: 0.4rem;
    }
    .badge-measured { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .badge-estimated { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
    .badge-unavailable { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }

    /* Visualizer Container & Box */
    .viewer-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 1rem;
    }
    .viewer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0.5rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid rgba(28, 43, 69, 0.6);
    }
    .viewer-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* Semantic Legend Pill */
    .legend-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.35rem 0.6rem;
        background: rgba(12, 19, 34, 0.7);
        border: 1px solid var(--border-subtle);
        border-radius: 6px;
        margin-bottom: 0.35rem;
        font-size: 0.78rem;
    }
    .legend-color-box {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        display: inline-block;
        margin-right: 0.5rem;
    }

    /* Terminal System Logs */
    .terminal-log-box {
        background: #04070d;
        border: 1px solid #1c2b45;
        border-radius: 6px;
        padding: 0.65rem 0.85rem;
        font-family: "JetBrains Mono", Consolas, monospace;
        font-size: 0.74rem;
        color: #94a3b8;
        max-height: 180px;
        overflow-y: auto;
        line-height: 1.5;
    }
    .terminal-log-line {
        display: flex;
        gap: 0.6rem;
    }
    .log-time { color: var(--accent-cyan); }
    .log-msg { color: #e2e8f0; }
    .log-tag { color: var(--accent-blue); }

    /* Summary Bar at Bottom */
    .summary-footer {
        background: #090e18;
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 1.5rem;
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        font-size: 0.78rem;
        color: var(--text-secondary);
        align-items: center;
    }
    .summary-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .summary-item strong {
        color: #ffffff;
    }
</style>
"""


def apply_custom_styles() -> None:
    """Inject workstation CSS rules into Streamlit DOM."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_dark_plotly_template() -> go.layout.Template:
    """
    Returns a unified Plotly dark engineering template matching the workstation.
    """
    template = go.layout.Template()
    template.layout = go.Layout(
        paper_bgcolor="#0c1322",
        plot_bgcolor="#0c1322",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            size=11,
            color="#94a3b8",
        ),
        title=dict(
            font=dict(color="#ffffff", size=13),
            x=0.02,
            y=0.96,
        ),
        xaxis=dict(
            gridcolor="#172338",
            linecolor="#1c2b45",
            tickcolor="#1c2b45",
            zerolinecolor="#22334f",
            showgrid=True,
        ),
        yaxis=dict(
            gridcolor="#172338",
            linecolor="#1c2b45",
            tickcolor="#1c2b45",
            zerolinecolor="#22334f",
            showgrid=True,
        ),
        scene=dict(
            xaxis=dict(
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
                linecolor="#22334f",
                showbackground=True,
                zerolinecolor="#00d4ff",
            ),
            yaxis=dict(
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
                linecolor="#22334f",
                showbackground=True,
                zerolinecolor="#3b82f6",
            ),
            zaxis=dict(
                backgroundcolor="#070b12",
                gridcolor="#1c2b45",
                linecolor="#22334f",
                showbackground=True,
                zerolinecolor="#10b981",
            ),
        ),
        margin=dict(l=25, r=25, t=35, b=25),
    )
    return template
