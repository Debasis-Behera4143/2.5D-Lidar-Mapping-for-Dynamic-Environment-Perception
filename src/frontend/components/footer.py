"""
Footer Information Strip Component.

Implements the bottom status bar matching the reference image:
- "What This Dashboard Shows" explanatory text
- Key semantic objects and their dynamic/drivability properties:
    * Left Wall: Non-drivable
    * Front Vehicle: Dynamic
    * Right Tree: Static
    * Grid Resolution: (5 cm / 10 cm / 25 cm / 50 cm)
    * Map Type: Semantic 2.5D Elevation
"""

import streamlit as st


def render_footer_strip() -> None:
    """
    Render bottom information strip matching reference screenshot.
    """
    footer_html = (
        '<div class="summary-footer">'
        '<div class="summary-left">'
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" style="flex-shrink: 0;">'
        '<circle cx="12" cy="12" r="10"></circle>'
        '<line x1="22" y1="12" x2="18" y2="12"></line>'
        '<line x1="6" y1="12" x2="2" y2="12"></line>'
        '<line x1="12" y1="6" x2="12" y2="2"></line>'
        '<line x1="12" y1="22" x2="12" y2="18"></line>'
        '</svg>'
        '<div>'
        '<strong>What This Dashboard Shows</strong><br>'
        '<span style="font-size: 0.70rem; color: #94a3b8;">'
        'A real-time simulation of LiDAR scene understanding, semantic classification, '
        'adaptive 2.5D mapping and system performance.'
        '</span>'
        '</div>'
        '</div>'
        '<div class="summary-right">'
        '<div class="summary-item">'
        '<span style="color: #ef4444; font-size: 0.9rem;">🧱</span>'
        '<div>'
        '<div style="font-weight: 600; color: #f8fafc;">Left Wall</div>'
        '<div style="font-size: 0.65rem; color: #ef4444;">Non-drivable</div>'
        '</div>'
        '</div>'
        '<div class="summary-item">'
        '<span style="color: #d946ef; font-size: 0.9rem;">🚗</span>'
        '<div>'
        '<div style="font-weight: 600; color: #f8fafc;">Front Vehicle</div>'
        '<div style="font-size: 0.65rem; color: #d946ef;">Dynamic</div>'
        '</div>'
        '</div>'
        '<div class="summary-item">'
        '<span style="color: #10b981; font-size: 0.9rem;">🌳</span>'
        '<div>'
        '<div style="font-weight: 600; color: #f8fafc;">Right Tree</div>'
        '<div style="font-size: 0.65rem; color: #10b981;">Static</div>'
        '</div>'
        '</div>'
        '<div class="summary-item">'
        '<span style="color: #00d4ff; font-size: 0.9rem;">▦</span>'
        '<div>'
        '<div style="font-weight: 600; color: #f8fafc;">Grid Resolution</div>'
        '<div style="font-size: 0.65rem; color: #00d4ff;">5 cm / 10 cm / 25 cm / 50 cm</div>'
        '</div>'
        '</div>'
        '<div class="summary-item">'
        '<span style="color: #a855f7; font-size: 0.9rem;">🗺️</span>'
        '<div>'
        '<div style="font-weight: 600; color: #f8fafc;">Map Type</div>'
        '<div style="font-size: 0.65rem; color: #a855f7;">Semantic 2.5D Elevation</div>'
        '</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(footer_html, unsafe_allow_html=True)
