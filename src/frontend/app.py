"""
Adaptive Variable-Resolution 2.5D LiDAR Mapping Engineering Workstation.

Main frontend entrypoint integrating:
- Dashboard: Executive perception workstation with 3D elevation map and adaptive grid benchmark
- Point Cloud Viewer: Interactive 3D LiDAR point cloud inspection with spatial bounds
- 2.5D Mapping: Coarse-to-fine variable-resolution quadtree grid maps & elevation profiles
- Semantic Analysis: Canonical 8-class taxonomy, point-wise distribution & confidence scoring
- Performance: Hardware-measured pipeline latencies, throughput FPS & cell reduction benchmarks
- Settings: Backend service connectivity, sample selector, and hyperparameter configuration
"""

import time
from typing import Any, Dict
import numpy as np
import pandas as pd
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Adaptive 2.5D LiDAR Mapping Workstation",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from src.frontend.api_client import ApiClient
from src.frontend.components.comparison_view import (
    render_comparison_view,
    render_dashboard_comparison_strip,
)
from src.frontend.components.footer import render_footer_strip
from src.frontend.components.header import render_header
from src.frontend.components.main_elevation_view import render_main_elevation_view
from src.frontend.components.map_view import (
    create_2d_grid_figure,
    create_elevation_profile_chart,
    render_map_view,
)
from src.frontend.components.performance_view import render_performance_view
from src.frontend.components.pointcloud_view import render_pointcloud_view
from src.frontend.components.right_side_panels import render_right_column_panels
from src.frontend.components.scene_overview_panel import render_scene_overview_panel
from src.frontend.components.semantic_view import render_semantic_view
from src.frontend.components.sidebar import render_sidebar
from src.frontend.config import BACKEND_API_URL
from src.frontend.data_adapter import add_system_log, init_session_state
from src.frontend.providers import FastAPIDataProvider, SimulationDataProvider
from src.frontend.styles import apply_custom_styles


def main() -> None:
    apply_custom_styles()
    init_session_state()

    client = ApiClient(base_url=BACKEND_API_URL)

    # 1. Health & Sample Discovery
    health_data = client.check_health()
    samples_list = client.get_samples() if health_data.get("online") else []

    # 2. Select Active Data Provider (Simulation vs Live FastAPI)
    is_simulation = st.session_state.get("data_source", "Simulation") == "Simulation"
    if is_simulation:
        provider = SimulationDataProvider()
    else:
        provider = FastAPIDataProvider(base_url=BACKEND_API_URL)

    # 3. Pipeline Handlers for Live Backend
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

    # 4. Render Top Header
    render_header(
        is_simulation=is_simulation,
        sample_meta=st.session_state.sample_metadata,
        backend_online=health_data.get("online", False),
        ping_ms=health_data.get("ping_ms"),
    )

    # 5. Render Sidebar Navigation & Hyperparameters
    current_page = render_sidebar(
        samples_list=samples_list,
        on_run_perception=handle_run_perception,
        on_run_mapping=handle_run_mapping,
        on_run_full_pipeline=handle_run_full_pipeline,
    )

    # 6. Route to Active Page View (Strictly 6 core pages)
    if current_page == "Dashboard":
        render_dashboard_page(provider=provider, is_simulation=is_simulation)
    elif current_page == "Point Cloud Viewer":
        render_pointcloud_page(provider=provider)
    elif current_page == "2.5D Mapping":
        render_mapping_page(provider=provider)
    elif current_page == "Semantic Analysis":
        render_semantic_page(provider=provider)
    elif current_page == "Performance":
        render_perf_page(provider=provider)
    elif current_page == "Settings":
        render_settings_page(client, health_data)


# ============================================================================
# PAGE IMPLEMENTATIONS
# ============================================================================

def render_dashboard_page(provider: Any, is_simulation: bool) -> None:
    """
    Main Executive LiDAR Perception Workstation.
    Focused, single-screen layout communicating:
    - Left column: Perception & Mapping Pipeline (5 research stages)
    - Center column: 2.5D Semantic Elevation Map with Driver, BEV, and Side presets
    - Right column: Semantic Taxonomy & Inferred Point Distribution + Resolution Bands
    - Bottom section: Direct Quantitative Benchmark (Uniform vs Adaptive Variable Grid)
    - Footer strip: Semantic properties & resolution reference
    """
    frame_id = st.session_state.get("selected_frame_id", "1248")

    # Ingest data from provider (simulation or FastAPI)
    perc = provider.get_perception_data(frame_id)
    ada_map = provider.get_adaptive_map(
        perc,
        base_resolution=st.session_state.base_resolution,
        fine_resolution=st.session_state.fine_resolution,
        importance_threshold=st.session_state.importance_threshold,
        dynamic_threshold=st.session_state.dynamic_threshold,
    )
    uni_map = provider.get_uniform_map(perc, resolution=st.session_state.fine_resolution)
    comp_data = provider.get_map_comparison(uni_map, ada_map)

    # Keep session state populated for other pages
    st.session_state.perception_result = perc
    st.session_state.adaptive_map_result = ada_map
    st.session_state.uniform_map_result = uni_map
    st.session_state.comparison_result = comp_data

    # ROW 1: PRIMARY 3-COLUMN WORKSTATION VIEW
    col_left, col_center, col_right = st.columns([1.8, 6.8, 2.7])

    with col_left:
        render_scene_overview_panel(perc)

    with col_center:
        render_main_elevation_view(perc, ada_map)

    with col_right:
        render_right_column_panels(perc, is_simulation=is_simulation)

    # ROW 2: CORE RESEARCH BENCHMARK (UNIFORM VS ADAPTIVE GRID)
    render_dashboard_comparison_strip(
        uniform_map=uni_map,
        adaptive_map=ada_map,
        comparison_metrics=comp_data,
    )

    # ROW 3: FOOTER STATUS STRIP
    render_footer_strip()


def render_pointcloud_page(provider: Any):
    st.markdown("### 3D LiDAR Point Cloud Inspection")
    st.markdown("Interactive point cloud viewer with spatial filtering, intensity inspection, and coordinate bounds.")

    frame_id = st.session_state.get("selected_frame_id", "1248")
    perc = st.session_state.perception_result or provider.get_perception_data(frame_id)

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

    pts = perc.get("points", [])
    if len(pts) > 0:
        pts_arr = pd.DataFrame(pts, columns=["x", "y", "z", "intensity"] if len(pts[0]) > 3 else ["x", "y", "z"])
        st.markdown("#### Point Cloud Geometric Bounds")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.metric("X Range (Forward)", f"[{pts_arr['x'].min():.1f}, {pts_arr['x'].max():.1f}] m")
        with b2:
            st.metric("Y Range (Lateral)", f"[{pts_arr['y'].min():.1f}, {pts_arr['y'].max():.1f}] m")
        with b3:
            st.metric("Z Range (Height)", f"[{pts_arr['z'].min():.1f}, {pts_arr['z'].max():.1f}] m")


def render_mapping_page(provider: Any):
    st.markdown("### 2.5D Adaptive Variable-Resolution Mapping")
    st.markdown(
        "Demonstrates recursive quadtree cell subdivision based on semantic importance "
        "and dynamic obstacle displacement."
    )

    frame_id = st.session_state.get("selected_frame_id", "1248")
    perc = st.session_state.perception_result or provider.get_perception_data(frame_id)
    ada_map = st.session_state.adaptive_map_result or provider.get_adaptive_map(perc)

    c1, c2 = st.columns([8, 2])
    with c2:
        st.markdown("#### Map Display Options")
        color_by = st.selectbox(
            "Color Cells By",
            ["Resolution Level", "Elevation (Height)", "Semantic Class", "Importance"],
            index=0,
        )
    with c1:
        render_map_view(ada_map, color_by=color_by)

    st.markdown("---")
    st.markdown("#### Cell Count & Spatial Statistics")
    cells = ada_map.get("cells", [])
    if cells:
        m1, m2, m3, m4 = st.columns(4)
        fine_cnt = sum(1 for c in cells if c.get("level") == "fine")
        coarse_cnt = len(cells) - fine_cnt
        with m1:
            st.metric("Active Cells (Sample)", f"{len(cells):,d}")
        with m2:
            st.metric("Fine Grid Cells (0.05-0.10m)", f"{fine_cnt:,d}")
        with m3:
            st.metric("Coarse Base Cells (0.25-0.50m)", f"{coarse_cnt:,d}")
        with m4:
            st.metric("Subdivision Ratio", f"{(fine_cnt / max(1, len(cells))) * 100:.1f}%")

    st.markdown("---")
    st.markdown("#### Longitudinal Elevation Profile (Height Z vs Forward Distance X)")
    pts = np.asarray(perc.get("points", []))
    if len(pts) > 0:
        fig_elev = create_elevation_profile_chart(pts, is_cells=False)
        st.plotly_chart(fig_elev, use_container_width=True, config={"displayModeBar": False})


def render_semantic_page(provider: Any):
    frame_id = st.session_state.get("selected_frame_id", "1248")
    perc = st.session_state.perception_result or provider.get_perception_data(frame_id)
    render_semantic_view(perc)


def render_perf_page(provider: Any):
    frame_id = st.session_state.get("selected_frame_id", "1248")
    perc = st.session_state.perception_result or provider.get_perception_data(frame_id)
    uni_map = st.session_state.uniform_map_result or provider.get_uniform_map(perc, resolution=st.session_state.fine_resolution)
    ada_map = st.session_state.adaptive_map_result or provider.get_adaptive_map(perc)
    comp = st.session_state.comparison_result or provider.get_map_comparison(uni_map, ada_map)
    timings = st.session_state.timings

    pts_cnt = len(perc.get("points", []))
    uni_cells = uni_map.get("cell_count", 0)
    ada_cells = ada_map.get("cell_count", 0)
    comp_metrics = comp.get("comparison", {})

    render_performance_view(
        timings=timings,
        point_count=pts_cnt,
        uniform_cells=uni_cells,
        adaptive_cells=ada_cells,
        comparison_metrics=comp_metrics,
    )


def render_settings_page(client: ApiClient, health_data: Dict[str, Any]):
    st.markdown("### Settings & Diagnostics")
    st.markdown("Workstation connectivity, backend status, and execution diagnostics.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Backend Service Health")
        st.json(health_data)
    with c2:
        st.markdown("#### Workstation Session Configuration")
        st.write({
            "data_source": st.session_state.get("data_source", "Simulation"),
            "selected_frame_id": st.session_state.get("selected_frame_id", "1248"),
            "base_resolution": st.session_state.base_resolution,
            "fine_resolution": st.session_state.fine_resolution,
            "importance_threshold": st.session_state.importance_threshold,
            "dynamic_threshold": st.session_state.dynamic_threshold,
            "backend_url": BACKEND_API_URL,
        })


if __name__ == "__main__":
    main()
