"""
Technical Metric Cards and KPI Indicators.

Renders high-density metric indicators with clear empirical labels:
- [MEASURED] for actual measured timings and counts
- [ESTIMATED] for analytical models (e.g. 64-byte cell struct memory)
- [UNAVAILABLE] or N/A when data is not produced
"""

from typing import Any, Dict, List, Optional
import streamlit as st


def render_metric_card(
    label: str,
    value: str,
    subtext: str = "",
    badge_type: str = "measured",  # 'measured', 'estimated', 'unavailable'
    badge_text: Optional[str] = None,
) -> None:
    """
    Render a single workstation KPI card with strict empirical provenance.
    """
    badge_cls = f"badge-{badge_type}"
    badge_lbl = badge_text or badge_type.upper()

    card_html = f"""
    <div class="metric-card">
        <div class="label">
            {label}
            <span class="metric-badge {badge_cls}">{badge_lbl}</span>
        </div>
        <div class="value">{value}</div>
        <div class="subtext">{subtext}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_circular_metric(
    label: str,
    value_str: str,
    subtext: str,
    percentage: float,
    color: str = "#00d4ff",
    badge_type: str = "measured",
) -> None:
    """
    Render a compact circular gauge card matching the reference dashboard style.
    """
    badge_cls = f"badge-{badge_type}"
    # SVG circle calculation (radius 36, circumference 226.2)
    circumference = 226.2
    offset = circumference * (1.0 - max(0.0, min(1.0, percentage / 100.0)))

    gauge_html = f"""
    <div class="metric-card" style="text-align: center; display: flex; flex-direction: column; align-items: center;">
        <div class="label" style="width: 100%; text-align: left;">
            {label}
            <span class="metric-badge {badge_cls}">{badge_type.upper()}</span>
        </div>
        <div style="position: relative; width: 88px; height: 88px; margin: 0.5rem 0;">
            <svg width="88" height="88" viewBox="0 0 88 88" style="transform: rotate(-90deg);">
                <circle cx="44" cy="44" r="36" stroke="#1c2b45" stroke-width="7" fill="none"></circle>
                <circle cx="44" cy="44" r="36" stroke="{color}" stroke-width="7" fill="none"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                    stroke-linecap="round"></circle>
            </svg>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                display: flex; align-items: center; justify-content: center;
                font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #ffffff;">
                {value_str}
            </div>
        </div>
        <div class="subtext">{subtext}</div>
    </div>
    """
    st.markdown(gauge_html, unsafe_allow_html=True)
