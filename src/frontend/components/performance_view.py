"""
Performance & Technical Benchmarking View.

Displays strictly empirical system performance metrics:
- End-to-end pipeline latency breakdown [MEASURED]
- Real-time execution FPS [MEASURED]
- Point throughput (points/second) [MEASURED]
- Cell count comparisons [MEASURED]
- Analytical struct memory footprint model [ESTIMATED]
- Explicit N/A / Unavailable labels for unmeasured metrics
"""

from typing import Any, Dict, Optional
import streamlit as st

from src.frontend.components.metric_cards import render_metric_card


def render_performance_view(
    timings: Dict[str, Optional[float]],
    point_count: int = 0,
    uniform_cells: int = 0,
    adaptive_cells: int = 0,
    comparison_metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render Technical Benchmarking and Performance Profiler screen.
    """
    st.markdown("### Technical Benchmarking & Performance Profiler")
    st.markdown(
        "Empirical runtime profiling across perception and mapping pipeline stages. "
        "Measured directly from hardware execution; no synthetic or marketing numbers."
    )

    inf_ms = timings.get("inference_ms")
    uni_ms = timings.get("uniform_mapping_ms")
    ada_ms = timings.get("adaptive_mapping_ms")
    comp_ms = timings.get("comparison_ms")
    tot_ms = timings.get("total_pipeline_ms")

    # Compute actual measured FPS if total latency is measured
    fps_val = round(1000.0 / tot_ms, 1) if tot_ms and tot_ms > 0 else None
    fps_str = f"{fps_val} FPS" if fps_val else "N/A"

    # KPI Row
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            label="Total Pipeline Latency",
            value=f"{tot_ms:.1f} ms" if tot_ms else "N/A",
            subtext="Inference + Adaptive Mapping + Metrics" if tot_ms else "Run pipeline to measure",
            badge_type="measured" if tot_ms else "unavailable",
        )

    with c2:
        render_metric_card(
            label="Throughput (FPS)",
            value=fps_str,
            subtext="Calculated from actual measured frame latency",
            badge_type="measured" if fps_val else "unavailable",
        )

    with c3:
        pts_per_sec = int((point_count / (tot_ms / 1000.0))) if tot_ms and tot_ms > 0 and point_count > 0 else None
        render_metric_card(
            label="Point Processing Throughput",
            value=f"{pts_per_sec:,d} pts/s" if pts_per_sec else "N/A",
            subtext=f"{point_count:,d} points in {tot_ms:.1f} ms" if tot_ms else "Awaiting execution",
            badge_type="measured" if pts_per_sec else "unavailable",
        )

    with c4:
        comp = comparison_metrics.get("comparison", {}) if comparison_metrics else {}
        mem_red = comp.get("estimated_memory_reduction_percent")
        render_metric_card(
            label="Memory Footprint Reduction",
            value=f"{mem_red:+.1f}%" if mem_red is not None else "N/A",
            subtext="Analytical 64-byte/cell struct model",
            badge_type="estimated" if mem_red is not None else "unavailable",
            badge_text="ESTIMATED",
        )

    st.markdown("---")
    st.markdown("#### Execution Latency Breakdown by Pipeline Stage")

    col_t1, col_t2 = st.columns(2)

    inf_str = f"{inf_ms:.1f} ms" if inf_ms is not None else "N/A"
    uni_str = f"{uni_ms:.1f} ms" if uni_ms is not None else "N/A"
    ada_str = f"{ada_ms:.1f} ms" if ada_ms is not None else "N/A"
    comp_str = f"{comp_ms:.1f} ms" if comp_ms is not None else "N/A"
    tot_str = f"{tot_ms:.1f} ms" if tot_ms is not None else "N/A"

    with col_t1:
        st.markdown(
            f"""
            | Pipeline Stage | Measured Latency | Status / Provenance |
            |---|---|---|
            | **AI Semantic Inference (RandLA-Net)** | `{inf_str}` | `[MEASURED]` Network forward pass |
            | **Uniform 2.5D Mapping** | `{uni_str}` | `[MEASURED]` Fixed-resolution binning |
            | **Adaptive 2.5D Mapping** | `{ada_str}` | `[MEASURED]` Coarse-to-fine subdivision |
            | **Map Comparison & Benchmarking** | `{comp_str}` | `[MEASURED]` Metric calculation |
            | **Full End-to-End Processing** | `{tot_str}` | `[MEASURED]` Sum of active pipeline stages |
            """
        )

    with col_t2:
        st.markdown(
            """
            | Unmeasured / Unavailable Metrics | Status | Rationale |
            |---|---|---|
            | **GPU VRAM Allocation** | `Unavailable` | CPU PyTorch runtime active; GPU VRAM profiling inactive. |
            | **Full Scene Flow / SLAM Drift** | `Unavailable` | Out of scope for SIH prototype (see SRS Section 4). |
            | **Production mIoU on Test Set** | `Unavailable` | Baseline prototype model trained for 1 epoch on limited data. |
            | **Real-World Vehicle Trajectory Preview** | `Unavailable` | Offline dataset replay; vehicle CAN bus inactive. |
            """
        )

    st.markdown("---")
    st.markdown("#### Spatial Discretization Benchmarks")

    cnt_pts = int(point_count) if isinstance(point_count, (int, float)) else 0
    cnt_uni = int(uniform_cells) if isinstance(uniform_cells, (int, float)) else 0
    cnt_ada = int(adaptive_cells) if isinstance(adaptive_cells, (int, float)) else 0

    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Total Ingested Points", f"{cnt_pts:,d}")
    with s2:
        st.metric("Uniform Grid Occupied Cells", f"{cnt_uni:,d}")
    with s3:
        st.metric("Adaptive Grid Occupied Cells", f"{cnt_ada:,d}")
