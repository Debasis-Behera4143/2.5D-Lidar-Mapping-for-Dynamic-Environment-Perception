"""
Workstation Header Component.

Renders the top application bar with system status, active dataset,
selected frame ID, and live API connectivity indicator.
"""

from datetime import datetime
from typing import Any, Dict, Optional
import streamlit as st


def render_header(
    health_data: Dict[str, Any],
    sample_meta: Optional[Dict[str, Any]] = None,
    processing_status: str = "Ready",
) -> None:
    """
    Render top technical workstation header.
    """
    is_online = health_data.get("online", False)
    ping = health_data.get("ping_ms")
    ping_str = f"{ping:.0f} ms" if ping is not None else "N/A"

    dataset_name = sample_meta.get("dataset_type", "None Selected") if sample_meta else "None Selected"
    frame_id = sample_meta.get("frame_id", "N/A") if sample_meta else "N/A"
    current_time = datetime.now().strftime("%H:%M:%S")

    online_badge = (
        f'<span class="status-pill online">● API Online ({ping_str})</span>'
        if is_online
        else '<span class="status-pill offline">● API Offline</span>'
    )

    proc_pill = (
        f'<span class="status-pill info">● {processing_status}</span>'
        if processing_status != "Processing"
        else '<span class="status-pill warning">● Computing...</span>'
    )

    header_html = f"""
    <div class="workstation-header">
        <div class="header-title-block">
            <h1>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                    <polyline points="2 17 12 22 22 17"></polyline>
                    <polyline points="2 12 12 17 22 12"></polyline>
                </svg>
                Adaptive 2.5D LiDAR Mapping Workstation
            </h1>
            <div class="header-subtitle">Semantic-Aware Dynamic Environment Perception</div>
        </div>
        <div class="header-badges">
            {online_badge}
            <span class="status-pill info">Dataset: {dataset_name}</span>
            <span class="status-pill info">Frame: {frame_id}</span>
            {proc_pill}
            <span class="status-pill info" style="color: #94a3b8;">{current_time}</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
