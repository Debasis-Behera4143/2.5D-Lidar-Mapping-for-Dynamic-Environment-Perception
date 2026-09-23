"""
Workstation Sidebar Component.

Provides:
- Page navigation selection
- Dataset & LiDAR sample frame picker
- Algorithmic hyperparameter controls (resolutions, thresholds)
- Visualization display filters (color modes, camera presets, class filters)
- Execution trigger buttons
"""

from typing import Any, Callable, Dict, List, Optional
import streamlit as st

from src.frontend.config import (
    CLASS_NAMES,
    DEFAULT_BASE_RESOLUTION,
    DEFAULT_DYNAMIC_THRESHOLD,
    DEFAULT_FINE_RESOLUTION,
    DEFAULT_IMPORTANCE_THRESHOLD,
    DEFAULT_NUM_POINTS,
    DEFAULT_PREVIEW_POINTS,
    PAGES,
)


def render_sidebar(
    samples_list: List[Dict[str, Any]],
    on_run_perception: Optional[Callable[[], None]] = None,
    on_run_mapping: Optional[Callable[[], None]] = None,
    on_run_full_pipeline: Optional[Callable[[], None]] = None,
) -> str:
    """
    Render sidebar navigation and workstation parameters.

    Returns:
        str: Selected page name.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <span style="font-weight: 700; font-size: 1.05rem; color: #ffffff;">LiDAR Perception</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Page Navigation
        selected_page = st.radio(
            "Navigation",
            PAGES,
            index=PAGES.index(st.session_state.get("current_page", "Dashboard"))
            if st.session_state.get("current_page") in PAGES else 0,
            key="page_radio",
            label_visibility="collapsed",
        )
        st.session_state.current_page = selected_page

        st.markdown("---")
        st.markdown("##### LiDAR Sample Frame")

        if len(samples_list) > 0:
            sample_options = [s["sample_id"] for s in samples_list]
            selected_idx = 0
            if st.session_state.selected_sample_id in sample_options:
                selected_idx = sample_options.index(st.session_state.selected_sample_id)

            chosen_sample_id = st.selectbox(
                "Select LiDAR Scan",
                sample_options,
                index=selected_idx,
                key="sample_selector",
            )
            st.session_state.selected_sample_id = chosen_sample_id

            # Locate sample metadata
            for s in samples_list:
                if s["sample_id"] == chosen_sample_id:
                    st.session_state.sample_metadata = s
                    break

            meta = st.session_state.sample_metadata
            if meta:
                has_labels_str = "Available" if meta.get("has_ground_truth") else "Missing"
                st.caption(
                    f"Dataset: **{meta.get('dataset_type')}** | Seq: **{meta.get('sequence_id')}**<br>"
                    f"Frame: **{meta.get('frame_id')}** | Points: **{meta.get('point_count', 0):,d}**<br>"
                    f"Ground Truth Labels: **{has_labels_str}**",
                    unsafe_allow_html=True,
                )
        else:
            st.warning("No LiDAR samples discovered in dataset directory.")

        st.markdown("---")
        st.markdown("##### Pipeline Hyperparameters")

        with st.expander("Mapping Resolutions", expanded=False):
            st.session_state.base_resolution = st.slider(
                "Base (Coarse) Resolution (m)",
                min_value=0.50, max_value=3.00, value=float(st.session_state.base_resolution), step=0.25,
                help="Resolution for planar ground, road, and distant static areas."
            )
            st.session_state.fine_resolution = st.slider(
                "Fine Resolution (m)",
                min_value=0.05, max_value=0.50, value=float(st.session_state.fine_resolution), step=0.05,
                help="Resolution for subdivided cells containing dynamic or critical objects."
            )
            st.session_state.importance_threshold = st.slider(
                "Importance Threshold",
                min_value=0.10, max_value=0.90, value=float(st.session_state.importance_threshold), step=0.05,
                help="Cutoff score above which coarse cells are recursively subdivided."
            )
            st.session_state.dynamic_threshold = st.slider(
                "Movement Threshold (m)",
                min_value=0.05, max_value=1.00, value=float(st.session_state.dynamic_threshold), step=0.05,
                help="Frame-to-frame displacement indicating moving obstacles."
            )

        with st.expander("Inference Settings", expanded=False):
            st.session_state.num_points = st.select_slider(
                "Inference Point Count",
                options=[1024, 2048, 4096, 8192],
                value=st.session_state.num_points,
                help="Target subsampled points for RandLA-Net neural forward pass."
            )
            st.session_state.preview_limit = st.slider(
                "3D View Downsampling Limit",
                min_value=1000, max_value=8000, value=int(st.session_state.preview_limit), step=500,
                help="Point cloud subsample size for silky smooth 60fps WebGL rendering."
            )

        with st.expander("Display & Filter Controls", expanded=False):
            st.session_state.color_mode = st.selectbox(
                "Point Color Mode",
                ["Semantic", "Elevation (Z)", "Intensity", "Error Map"],
                index=["Semantic", "Elevation (Z)", "Intensity", "Error Map"].index(st.session_state.color_mode),
            )
            st.session_state.view_preset = st.selectbox(
                "Camera Preset",
                ["3D Perspective", "Top View (BEV)", "Side View"],
                index=["3D Perspective", "Top View (BEV)", "Side View"].index(st.session_state.view_preset),
            )
            st.session_state.confidence_threshold = st.slider(
                "Min Confidence Filter",
                min_value=0.0, max_value=0.95, value=float(st.session_state.confidence_threshold), step=0.05,
            )
            st.session_state.selected_classes = st.multiselect(
                "Filter Semantic Classes",
                options=list(CLASS_NAMES.keys()),
                default=st.session_state.selected_classes,
                format_func=lambda x: f"{x}: {CLASS_NAMES[x].capitalize()}",
            )
            c_chk1, c_chk2 = st.columns(2)
            with c_chk1:
                st.session_state.show_bboxes = st.checkbox("Bounding Boxes", value=st.session_state.show_bboxes)
            with c_chk2:
                st.session_state.show_axes = st.checkbox("Axes & Grid", value=st.session_state.show_axes)

        st.markdown("---")
        st.markdown("##### Execute Pipeline")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("AI Perception", use_container_width=True, type="secondary"):
                if on_run_perception:
                    on_run_perception()
        with b2:
            if st.button("2.5D Mapping", use_container_width=True, type="secondary"):
                if on_run_mapping:
                    on_run_mapping()

        if st.button("Run Full Pipeline", use_container_width=True, type="primary"):
            if on_run_full_pipeline:
                on_run_full_pipeline()

    return selected_page
