"""
Terrain Analysis & Elevation Profile View.

Displays:
- Longitudinal elevation profile (Height Z vs Forward Distance X along vehicle heading)
- Lateral elevation profile (Height Z vs Lateral Distance Y)
- Ground elevation statistics: Min, Max, Mean height, Height variance
- Elevation distribution histogram
"""

from typing import Any, Dict, List, Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.frontend.styles import get_dark_plotly_template


def create_elevation_profile_chart(
    points_or_cells: np.ndarray,
    is_cells: bool = False,
) -> go.Figure:
    """
    Construct Longitudinal Elevation Profile chart (Height vs Distance).
    """
    fig = go.Figure()

    if len(points_or_cells) == 0:
        fig.update_layout(
            template=get_dark_plotly_template(),
            annotations=[
                dict(
                    text="No spatial elevation data available.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#64748b"),
                )
            ],
            height=300,
        )
        return fig

    if is_cells:
        # Extract from cells: X center and Mean Height
        x = points_or_cells[:, 0]
        z = points_or_cells[:, 1]
    else:
        # Extract from points
        x = points_or_cells[:, 0]
        z = points_or_cells[:, 2]

    # Filter forward trajectory (X >= 0) up to 80m
    forward_mask = (x >= 0) & (x <= 80)
    fx = x[forward_mask]
    fz = z[forward_mask]

    if len(fx) == 0:
        fx = x
        fz = z

    # Bin into 1m longitudinal distance slices to get smooth profile
    bins = np.linspace(0, max(10.0, float(np.max(fx))), num=50)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    indices = np.digitize(fx, bins) - 1

    profile_z = []
    min_z_profile = []
    max_z_profile = []

    for i in range(len(bin_centers)):
        slice_mask = (indices == i)
        if np.any(slice_mask):
            profile_z.append(float(np.mean(fz[slice_mask])))
            min_z_profile.append(float(np.min(fz[slice_mask])))
            max_z_profile.append(float(np.max(fz[slice_mask])))
        else:
            prev = profile_z[-1] if len(profile_z) > 0 else 0.0
            profile_z.append(prev)
            min_z_profile.append(prev)
            max_z_profile.append(prev)

    # Filled area chart matching reference dashboard
    fig.add_trace(
        go.Scatter(
            x=bin_centers,
            y=profile_z,
            mode="lines",
            line=dict(color="#00d4ff", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(0, 212, 255, 0.15)",
            name="Mean Elevation",
            hoverinfo="x+y",
        )
    )

    template = get_dark_plotly_template()
    fig.update_layout(
        template=template,
        xaxis=dict(title="Forward Distance X (m)", zeroline=True, zerolinecolor="#1e293b"),
        yaxis=dict(title="Height Z (m)", zeroline=True, zerolinecolor="#1e293b"),
        margin=dict(l=20, r=20, t=25, b=25),
        height=300,
        showlegend=False,
    )
    return fig


def render_terrain_view(
    perception_dict: Dict[str, Any],
    grid_map: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render complete Terrain Analysis page.
    """
    st.markdown("### Terrain Analysis & Elevation Profiles")
    st.markdown(
        "Empirical geometric elevation variations derived directly from LiDAR sensor returns "
        "and 2.5D cell aggregations. No synthetic slope or unverified friction models."
    )

    if not perception_dict or "points" not in perception_dict:
        st.warning("No LiDAR point cloud available. Ingest a scan frame to inspect terrain.")
        return

    pts = np.asarray(perception_dict["points"])
    z_vals = pts[:, 2]

    # Metrics
    min_h = float(np.min(z_vals))
    max_h = float(np.max(z_vals))
    mean_h = float(np.mean(z_vals))
    var_h = float(np.var(z_vals))
    std_h = float(np.std(z_vals))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Min Elevation (Z)", f"{min_h:.2f} m")
    with c2:
        st.metric("Max Elevation (Z)", f"{max_h:.2f} m")
    with c3:
        st.metric("Mean Height (Z)", f"{mean_h:.2f} m")
    with c4:
        st.metric("Height Variance (σ²)", f"{var_h:.3f} m²", help=f"Standard Deviation: {std_h:.2f} m")

    st.markdown("---")
    st.markdown("#### Longitudinal Elevation Profile (Front View along Forward Heading)")
    prof_fig = create_elevation_profile_chart(pts, is_cells=False)
    st.plotly_chart(prof_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Height (Z) Distribution")
        hist_fig = go.Figure(
            go.Histogram(
                x=z_vals,
                nbinsx=40,
                marker=dict(color="#3b82f6", line=dict(color="#1c2b45", width=1)),
            )
        )
        template = get_dark_plotly_template()
        hist_fig.update_layout(
            template=template,
            xaxis=dict(title="Height Z (m)"),
            yaxis=dict(title="Point Count"),
            margin=dict(l=20, r=20, t=20, b=25),
            height=280,
        )
        st.plotly_chart(hist_fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown("#### 2.5D Cell Height Statistics")
        if grid_map and "cells" in grid_map and len(grid_map["cells"]) > 0:
            cell_h = [c.get("mean_height", 0.0) for c in grid_map["cells"]]
            st.markdown(
                f"""
                - **Active Aggregated Cells**: `{len(cell_h):,d}`
                - **Cell Mean Elevation**: `{np.mean(cell_h):.2f} m`
                - **Cell Elevation Range**: `[{np.min(cell_h):.2f} m, {np.max(cell_h):.2f} m]`
                - **Cell Elevation StdDev**: `{np.std(cell_h):.2f} m`
                """
            )
            st.info(
                "Each 2.5D cell retains continuous height statistics (z_min, z_max, z_mean, "
                "z_variance) rather than discretizing vertical space into redundant 3D voxels."
            )
        else:
            st.info("Generate 2.5D map to view cell-aggregated height distributions.")
