"""
Adaptive Variable-Resolution 2.5D LiDAR Mapping Engineering Workstation.

Main frontend entrypoint integrating:
- Dashboard (Executive multi-view perception workstation)
- Point Cloud Viewer (Interactive 3D LiDAR point cloud)
- 2.5D Mapping (Adaptive coarse-to-fine variable-resolution grid)
- Semantic View (8-class taxonomy & confidence distribution)
- Terrain Analysis (Longitudinal elevation profiles & statistics)
- Object Analysis (Semantic point counts vs spatial candidate clusters)
- Performance (Empirical benchmarking & latency breakdown)
- Settings & Diagnostics (Backend health & checkpoint inspector)
"""

import time
from typing import Any, Dict
import pandas as pd
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Adaptive 2.5D LiDAR Mapping",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.frontend.api_client import ApiClient
from src.frontend.components.comparison_view import render_comparison_view
from src.frontend.components.header import render_header
from src.frontend.components.map_view import create_2d_grid_figure, render_map_view
from src.frontend.components.metric_cards import render_circular_metric, render_metric_card
from src.frontend.components.object_view import render_object_view
from src.frontend.components.performance_view import render_performance_view
from src.frontend.components.pointcloud_view import create_pointcloud_figure, render_pointcloud_view
from src.frontend.components.semantic_view import render_semantic_legend_panel, render_semantic_view
from src.frontend.components.sidebar import render_sidebar
from src.frontend.components.terrain_view import create_elevation_profile_chart, render_terrain_view
from src.frontend.config import BACKEND_API_URL
from src.frontend.data_adapter import add_system_log, init_session_state
from src.frontend.styles import apply_custom_styles, get_dark_plotly_template


def main() -> None:
    apply_custom_styles()
    init_session_state()

    client = ApiClient(base_url=BACKEND_API_URL)

    # 1. Health & Sample Discovery
    health_data = client.check_health()
    samples_list = client.get_samples() if health_data.get("online") else []

    # 2. Pipeline Execution Handlers
    def handle_run_perception():
        meta = st.session_state.sample_metadata
        if not meta:
            st.error("No sample selected.")
            return

        bin_path = meta.get("bin_path") or meta.get("point_cloud_path")
        lbl_path = meta.get("label_path")

        add_system_log(f"Running perception on scan {meta.get('frame_id')} ({meta.get('dataset_type')})...", tag="PERCEPTION")

        start_t = time.perf_counter()
        resp = client.run_inference(
            bin_path=bin_path,
            label_path=lbl_path,
            num_points=st.session_state.num_points,
            preview_points_limit=st.session_state.preview_limit,
        )
        latency = (time.perf_counter() - start_t) * 1000.0

        if resp.get("_success", False):
            st.session_state.previous_perception_result = st.session_state.perception_result
            st.session_state.perception_result = resp
            st.session_state.timings["inference_ms"] = round(latency, 1)
            pts_cnt = resp.get("total_points", 0)
            add_system_log(f"Inference complete: {pts_cnt:,d} points processed in {latency:.1f} ms.", tag="PERCEPTION")
            st.toast("Perception inference succeeded!", icon="✅")
        else:
            add_system_log(f"Inference failed: {resp.get('error')}", tag="ERROR")
            st.error(f"Inference error: {resp.get('error')}")

    def handle_run_mapping():
        perc = st.session_state.perception_result
        if not perc:
            st.warning("Please run perception first or select a sample frame.")
            return

        add_system_log("Generating uniform and adaptive 2.5D grid maps...", tag="MAPPING")

        # 1. Uniform Map
        start_u = time.perf_counter()
        uni_resp = client.generate_uniform_map(
            perception_payload=perc,
            resolution=st.session_state.fine_resolution,
        )
        uni_ms = (time.perf_counter() - start_u) * 1000.0

        if not uni_resp.get("_success", False):
            st.error(f"Uniform mapping failed: {uni_resp.get('error')}")
            return
        st.session_state.uniform_map_result = uni_resp
        st.session_state.timings["uniform_mapping_ms"] = round(uni_ms, 1)

        # 2. Adaptive Map
        start_a = time.perf_counter()
        ada_resp = client.generate_adaptive_map(
            perception_payload=perc,
            previous_payload=st.session_state.previous_perception_result,
            base_resolution=st.session_state.base_resolution,
            fine_resolution=st.session_state.fine_resolution,
            importance_threshold=st.session_state.importance_threshold,
            dynamic_threshold=st.session_state.dynamic_threshold,
        )
        ada_ms = (time.perf_counter() - start_a) * 1000.0

        if not ada_resp.get("_success", False):
            st.error(f"Adaptive mapping failed: {ada_resp.get('error')}")
            return
        st.session_state.adaptive_map_result = ada_resp
        st.session_state.timings["adaptive_mapping_ms"] = round(ada_ms, 1)

        # 3. Compare Maps
        start_c = time.perf_counter()
        comp_resp = client.compare_maps(uni_resp, ada_resp)
        comp_ms = (time.perf_counter() - start_c) * 1000.0
        st.session_state.comparison_result = comp_resp
        st.session_state.timings["comparison_ms"] = round(comp_ms, 1)

        inf_ms = st.session_state.timings.get("inference_ms", 0.0) or 0.0
        total_ms = inf_ms + ada_ms + comp_ms
        st.session_state.timings["total_pipeline_ms"] = round(total_ms, 1)

        red_pct = comp_resp.get("comparison", {}).get("cell_count_reduction_percent", 0.0)
        add_system_log(
            f"Mapping complete: Adaptive cells {ada_resp.get('cell_count', 0):,d}, "
            f"Reduction {red_pct:+.1f}%, latency {total_ms:.1f} ms.",
            tag="MAPPING",
        )
        st.toast(f"Adaptive 2.5D Mapping generated! Reduction: {red_pct:+.1f}%", icon="🗺️")

    def handle_run_full_pipeline():
        handle_run_perception()
        if st.session_state.perception_result:
            handle_run_mapping()

    # 3. Render Top Workstation Header
    proc_status = "Processing" if False else ("Ready" if health_data.get("online") else "Backend Offline")
    render_header(health_data, st.session_state.sample_metadata, processing_status=proc_status)

    # 4. Render Sidebar Navigation
    current_page = render_sidebar(
        samples_list=samples_list,
        on_run_perception=handle_run_perception,
        on_run_mapping=handle_run_mapping,
        on_run_full_pipeline=handle_run_full_pipeline,
    )

    # If backend is offline, show non-intrusive warning banner
    if not health_data.get("online"):
        st.warning(
            "⚠️ **Backend Service Offline**: FastAPI could not be reached at `"
            f"{BACKEND_API_URL}`. Start the backend with `uvicorn src.backend.app:app` to run perception and mapping."
        )

    # 5. Route to Active Page View
    if current_page == "Dashboard":
        render_dashboard_page()
    elif current_page == "Point Cloud Viewer":
        render_pointcloud_page()
    elif current_page == "2.5D Mapping":
        render_mapping_page()
    elif current_page == "Semantic View":
        render_semantic_page()
    elif current_page == "Terrain Analysis":
        render_terrain_page()
    elif current_page == "Object Analysis":
        render_object_page()
    elif current_page == "Performance":
        render_perf_page()
    elif current_page == "Settings":
        render_settings_page(client, health_data)


# ============================================================================
# PAGE IMPLEMENTATIONS
# ============================================================================

def render_dashboard_page():
    """
    Main Overview Dashboard matching Reference Images 1 and 2.
    """
    perc = st.session_state.perception_result
    uni_map = st.session_state.uniform_map_result
    ada_map = st.session_state.adaptive_map_result
    comp = st.session_state.comparison_result
    timings = st.session_state.timings

    # Top Pipeline Architecture Summary Bar
    st.markdown(
        """
        <div style="background: rgba(12, 19, 34, 0.7); border: 1px solid #1c2b45; border-radius: 6px;
            padding: 0.5rem 1rem; margin-bottom: 0.85rem; display: flex; align-items: center; justify-content: space-between; font-size: 0.78rem;">
            <div>
                <span style="color: #64748b; font-weight: 600;">PIPELINE FLOW:</span>
                <span style="color: #00d4ff; margin-left: 0.5rem;">LiDAR Data</span> →
                <span style="color: #3b82f6;">AI Semantic Segmentation (RandLA-Net)</span> →
                <span style="color: #f59e0b;">Importance & Movement Estimation</span> →
                <span style="color: #10b981; font-weight: 700;">Adaptive Variable-Resolution 2.5D Map</span>
            </div>
            <div style="color: #94a3b8;">
                SIH 2026 Core Innovation: Coarse-to-Fine Adaptive Cells
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Row 1: Main 3D LiDAR Viewer (Left, 70%) & Semantic Legend (Right, 30%)
    col_main, col_legend = st.columns([7, 3])

    with col_main:
        st.markdown(
            """
            <div class="viewer-header">
                <div class="viewer-title">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2">
                        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                    </svg>
                    3D Point Cloud with Semantic Labels (Adaptive 2.5D Representation)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if perc:
            render_pointcloud_view(
                perception_dict=perc,
                color_mode=st.session_state.color_mode,
                view_preset=st.session_state.view_preset,
                selected_classes=st.session_state.selected_classes,
                min_confidence=st.session_state.confidence_threshold,
                preview_limit=st.session_state.preview_limit,
                show_bboxes=st.session_state.show_bboxes,
                show_axes=st.session_state.show_axes,
            )
        else:
            st.info("👈 Select a LiDAR sample frame and click **Run Full Pipeline** in the sidebar to visualize.")

    with col_legend:
        # Semantic Legend
        class_dist = perc.get("class_distribution", {}) if perc else {}
        total_pts = perc.get("total_points", 0) if perc else 0
        render_semantic_legend_panel(class_dist, total_pts)

        # Adaptive Grid Resolution Legend (matching reference screenshot)
        st.markdown(
            """
            <div class="viewer-title" style="margin: 0.85rem 0 0.5rem 0;">Adaptive Grid Resolution Guide</div>
            <div class="legend-row">
                <div style="display: flex; align-items: center;">
                    <span class="legend-color-box" style="background-color: #f59e0b;"></span>
                    <span style="font-weight: 600; color: #ffffff;">Fine Grid (0.05 - 0.25 m)</span>
                </div>
                <div style="color: #fbbf24; font-size: 0.72rem;">Vulnerable / Dynamic Objects</div>
            </div>
            <div class="legend-row">
                <div style="display: flex; align-items: center;">
                    <span class="legend-color-box" style="background-color: #3b82f6;"></span>
                    <span style="font-weight: 600; color: #ffffff;">Base Grid (0.50 - 1.00 m)</span>
                </div>
                <div style="color: #60a5fa; font-size: 0.72rem;">Planar Road / Static Terrain</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Row 2: Secondary Visualizations Grid (matching Reference Screenshot 1 & 2)
    st.markdown("---")
    st.markdown("#### Secondary 2.5D Perception Views & Metrics")

    r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])

    with r2_c1:
        st.markdown(
            '<div class="viewer-title">2.5D Semantic Map (Top View)</div>',
            unsafe_allow_html=True,
        )
        if ada_map:
            fig_map = create_2d_grid_figure(ada_map, color_by="Semantic Class")
            fig_map.update_layout(height=280)
            st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Awaiting 2.5D map generation.")

    with r2_c2:
        st.markdown(
            '<div class="viewer-title">2.5D Elevation Profile (Front View)</div>',
            unsafe_allow_html=True,
        )
        if perc and "points" in perc:
            prof_fig = create_elevation_profile_chart(perc["points"], is_cells=False)
            prof_fig.update_layout(height=280)
            st.plotly_chart(prof_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Awaiting LiDAR scan ingestion.")

    with r2_c3:
        st.markdown(
            '<div class="viewer-title">Grid Comparison (Uniform vs Adaptive)</div>',
            unsafe_allow_html=True,
        )
        if comp and ada_map:
            fig_comp = create_2d_grid_figure(ada_map, color_by="Resolution Level")
            fig_comp.update_layout(height=280)
            st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Run mapping to view comparison.")

    # Row 3: Performance Metrics & System Activity Logs
    st.markdown("---")
    col_kpis, col_logs = st.columns([6, 4])

    with col_kpis:
        st.markdown('<div class="viewer-title">System Performance & Latency</div>', unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)

        inf_ms = timings.get("inference_ms")
        tot_ms = timings.get("total_pipeline_ms")
        fps_val = round(1000.0 / tot_ms, 1) if tot_ms and tot_ms > 0 else None

        with k1:
            tot_str = f"{tot_ms:.0f} ms" if tot_ms else "N/A"
            render_circular_metric("Latency", tot_str, "End-to-End Latency", percentage=min(100, tot_ms or 0), color="#3b82f6", badge_type="measured" if tot_ms else "unavailable")
        with k2:
            fps_str = f"{fps_val}" if fps_val else "N/A"
            render_circular_metric("Throughput", fps_str, "Computed FPS", percentage=min(100, (fps_val or 0) * 3), color="#00d4ff", badge_type="measured" if fps_val else "unavailable")
        with k3:
            red_pct = comp.get("comparison", {}).get("cell_count_reduction_percent") if comp else None
            red_str = f"{red_pct:+.0f}%" if red_pct is not None else "N/A"
            render_circular_metric("Reduction", red_str, "Spatial Cell Savings", percentage=abs(red_pct or 0), color="#10b981", badge_type="measured" if red_pct is not None else "unavailable")
        with k4:
            pts_cnt = perc.get("total_points", 0) if perc else 0
            pts_str = f"{pts_cnt:,d}" if pts_cnt > 0 else "N/A"
            render_circular_metric("Points", pts_str, "Active Scan Points", percentage=min(100, pts_cnt / 40.0), color="#f59e0b", badge_type="measured" if pts_cnt > 0 else "unavailable")

    with col_logs:
        st.markdown('<div class="viewer-title">System Activity Logs</div>', unsafe_allow_html=True)
        log_entries = st.session_state.get("logs", [])
        log_lines = []
        for entry in reversed(log_entries[-8:]):
            log_lines.append(
                f'<div class="terminal-log-line">'
                f'<span class="log-time">[{entry["time"]}]</span> '
                f'<span class="log-tag">[{entry["tag"]}]</span> '
                f'<span class="log-msg">{entry["msg"]}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div class="terminal-log-box">{"".join(log_lines)}</div>',
            unsafe_allow_html=True,
        )

    # Bottom Summary Bar
    st.markdown(
        """
        <div class="summary-footer">
            <div class="summary-item"><strong>Adaptive 2.5D Mapping:</strong> Subdivides critical dynamic obstacles into fine cells</div>
            <div class="summary-item"><strong>Perception Model:</strong> RandLA-Net (8 canonical classes)</div>
            <div class="summary-item"><strong>Coordinate Frame:</strong> Ego-vehicle centered (X=Forward, Y=Left, Z=Up)</div>
            <div class="summary-item"><strong>Point Conservation:</strong> 1:1 Strict Accounting</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pointcloud_page():
    st.markdown("### 3D LiDAR Point Cloud Inspection")
    perc = st.session_state.perception_result

    if not perc:
        st.warning("No LiDAR point cloud available. Run perception from the sidebar.")
        return

    render_pointcloud_view(
        perception_dict=perc,
        color_mode=st.session_state.color_mode,
        view_preset=st.session_state.view_preset,
        selected_classes=st.session_state.selected_classes,
        min_confidence=st.session_state.confidence_threshold,
        preview_limit=st.session_state.preview_limit,
        show_bboxes=st.session_state.show_bboxes,
        show_axes=st.session_state.show_axes,
    )

    # Spatial Bounds
    bounds = perc.get("spatial_bounds", {})
    st.markdown("#### Point Cloud Spatial Bounding Box")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.write(f"**X (Forward)**: `[{bounds.get('min_x', 0):.2f} m, {bounds.get('max_x', 0):.2f} m]`")
    with b2:
        st.write(f"**Y (Lateral)**: `[{bounds.get('min_y', 0):.2f} m, {bounds.get('max_y', 0):.2f} m]`")
    with b3:
        st.write(f"**Z (Vertical)**: `[{bounds.get('min_z', 0):.2f} m, {bounds.get('max_z', 0):.2f} m]`")


def render_mapping_page():
    ada_map = st.session_state.adaptive_map_result
    uni_map = st.session_state.uniform_map_result
    comp = st.session_state.comparison_result

    st.markdown("### Adaptive Variable-Resolution 2.5D Mapping")
    st.markdown(
        "Flagship variable-resolution grid representation. High-importance regions "
        "(pedestrians, vehicles, poles, dynamic obstacles) receive fine spatial discretization, "
        "while flat planar road surfaces are preserved at coarse base resolution."
    )

    if not ada_map:
        st.warning("No 2.5D map generated. Click '2.5D Mapping' in the sidebar.")
        return

    # View options
    color_opt = st.radio(
        "Color Grid Cells By:",
        ["Resolution Level", "Elevation (Height)", "Semantic Class", "Importance"],
        horizontal=True,
    )

    render_map_view(ada_map, color_by=color_opt)

    if uni_map and comp:
        st.markdown("---")
        render_comparison_view(uni_map, ada_map, comp)


def render_semantic_page():
    perc = st.session_state.perception_result
    render_semantic_view(perc)


def render_terrain_page():
    perc = st.session_state.perception_result
    grid = st.session_state.adaptive_map_result
    render_terrain_view(perc, grid)


def render_object_page():
    perc = st.session_state.perception_result
    render_object_view(perc)


def render_perf_page():
    timings = st.session_state.timings
    perc = st.session_state.perception_result
    uni_map = st.session_state.uniform_map_result
    ada_map = st.session_state.adaptive_map_result
    comp = st.session_state.comparison_result

    pts_cnt = perc.get("total_points", 0) if perc else 0
    u_cells = uni_map.get("cell_count", 0) if uni_map else 0
    a_cells = ada_map.get("cell_count", 0) if ada_map else 0

    render_performance_view(timings, point_count=pts_cnt, uniform_cells=u_cells, adaptive_cells=a_cells, comparison_metrics=comp)


def render_settings_page(client: ApiClient, health_data: Dict[str, Any]):
    st.markdown("### Workstation Settings & Diagnostics")

    st.markdown("#### Backend Service Health")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**API Base URL**: `{client.base_url}`")
        st.write(f"**System Status**: `{health_data.get('status', 'offline').upper()}`")
    with c2:
        dev_info = health_data.get("device_info", {})
        st.write(f"**Compute Device**: `{dev_info.get('device_name', 'CPU')}`")
        st.write(f"**PyTorch Version**: `{dev_info.get('torch_version', 'N/A')}`")
    with c3:
        ckpt_info = health_data.get("checkpoint_status", {})
        ckpt_exists = ckpt_info.get("exists", False)
        st.write(f"**Model Checkpoint**: `{'Available' if ckpt_exists else 'Missing'}`")
        st.write(f"**Model Type**: `{ckpt_info.get('model_type', 'RandLA-Net')}`")

    st.markdown("---")
    st.markdown("#### Raw API Diagnostics")
    with st.expander("Inspect Raw /api/v1/health Response"):
        st.json(health_data)


if __name__ == "__main__":
    main()
