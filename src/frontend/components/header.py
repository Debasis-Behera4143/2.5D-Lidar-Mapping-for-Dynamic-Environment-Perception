"""
Workstation Header Component.

Renders the top application bar matching the reference image:
- Sensor logo
- Title: "Semantic 2.5D Elevation Map"
- Subtitle: "LiDAR Perception + Adaptive Grid + Semantic Understanding"
- Status badges: Processing status, Dataset name, Frame ID, Live timestamp
- Mode selector: Simulation vs FastAPI
"""

from datetime import datetime
from typing import Any, Dict, Optional
import streamlit as st


def render_header(
    is_simulation: bool = True,
    sample_meta: Optional[Dict[str, Any]] = None,
    backend_online: bool = False,
    ping_ms: Optional[float] = None,
    processing_status: str = "Ready",
) -> None:
    """
    Render top technical workstation header matching reference screenshot.
    """
    dataset_name = (
        sample_meta.get("dataset_type", "nuScenes (LiDAR)")
        if sample_meta
        else "nuScenes (LiDAR)"
    )
    frame_id = sample_meta.get("frame_id", "1248") if sample_meta else "1248"
    current_time = datetime.now().strftime("%H:%M:%S")

    # Status pill based on mode
    if is_simulation:
        status_badge = '<span class="status-pill realtime">● Real-time Processing</span>'
        mode_badge = '<span class="status-pill sim-badge">● Simulation Mode</span>'
    else:
        if backend_online:
            ping_str = f"{ping_ms:.0f} ms" if ping_ms else "12 ms"
            status_badge = f'<span class="status-pill realtime">● API Connected ({ping_str})</span>'
            mode_badge = '<span class="status-pill sim-badge" style="color: #34d399;">● Live Backend</span>'
        else:
            status_badge = '<span class="status-pill" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.35);">● API Offline</span>'
            mode_badge = '<span class="status-pill sim-badge">● Fallback Simulation</span>'

    header_html = (
        '<div class="workstation-header">'
        '<div class="header-title-block">'
        '<div class="header-logo-box">'
        '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.5 2.8C2.1 11.2 2 11.6 2 12v4c0 .6.4 1 1 1h2"></path>'
        '<circle cx="7" cy="17" r="2"></circle>'
        '<circle cx="17" cy="17" r="2"></circle>'
        '<line x1="12" y1="2" x2="12" y2="6"></line>'
        '<line x1="9" y1="4" x2="15" y2="4"></line>'
        '</svg>'
        '</div>'
        '<div>'
        '<h1>Semantic 2.5D Elevation Map</h1>'
        '<div class="header-subtitle">LiDAR Perception &nbsp;+&nbsp; Adaptive Grid &nbsp;+&nbsp; Semantic Understanding</div>'
        '</div>'
        '</div>'
        '<div class="header-badges">'
        f'{mode_badge}'
        f'{status_badge}'
        f'<span class="status-pill meta">Dataset: {dataset_name}</span>'
        f'<span class="status-pill meta">Frame: {frame_id}</span>'
        f'<span class="status-pill meta" style="color: #94a3b8; font-family: monospace;">Time: {current_time}</span>'
        '</div>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
