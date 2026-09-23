"""
Object Analysis & Candidate Cluster Estimation View.

Strictly distinguishes:
- Semantic Class Point Counts (point-level classifications from RandLA-Net)
- Geometric Candidate Object Clusters (spatial DBSCAN clusters with 3D bounding boxes)
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import streamlit as st

from src.frontend.config import CLASS_COLORS, CLASS_NAMES
from src.frontend.data_adapter import extract_candidate_clusters


def render_object_view(
    perception_dict: Dict[str, Any],
) -> None:
    """
    Render Object Analysis page with strict technical differentiation.
    """
    st.markdown("### Object Analysis: Semantic Classes vs Spatial Clusters")

    st.info(
        "**Technical Disclosure (SRS Compliance)**: The perception network performs point-wise "
        "semantic segmentation. To assist dynamic environment perception without fabricating a full "
        "3D bounding-box detector, spatial candidate clusters are computed via Euclidean DBSCAN "
        "over classified obstacle points (vehicles, pedestrians, poles)."
    )

    if not perception_dict or "points" not in perception_dict:
        st.warning("No LiDAR point cloud available. Run inference on a sample frame.")
        return

    pts = np.asarray(perception_dict["points"])
    lbls = np.asarray(perception_dict.get("predicted_labels", []))
    class_dist = perception_dict.get("class_distribution", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 1. Semantic Point Counts (PointNet / RandLA-Net)")
        object_classes = ["vehicle", "pedestrian", "pole_sign", "other"]
        table_rows = []
        for c_name in object_classes:
            cnt = class_dist.get(c_name, 0)
            table_rows.append({
                "Semantic Class": c_name.capitalize(),
                "Point Count": f"{cnt:,d}",
                "Classification Type": "Point-wise Softmax Prediction",
            })
        st.table(pd.DataFrame(table_rows))

    with col2:
        st.markdown("#### 2. Candidate 3D Spatial Clusters (DBSCAN)")
        clusters = extract_candidate_clusters(pts, lbls, target_classes=[4, 5, 6])
        st.markdown(f"**Total Candidate Obstacles Detected**: `{len(clusters)}`")

        cluster_summary: Dict[str, int] = {}
        for c in clusters:
            c_name = c["class_name"]
            cluster_summary[c_name] = cluster_summary.get(c_name, 0) + 1

        summary_rows = []
        for c_id in [4, 5, 6]:
            c_name = CLASS_NAMES.get(c_id, f"class_{c_id}")
            cnt = cluster_summary.get(c_name, 0)
            summary_rows.append({
                "Object Class": c_name.capitalize(),
                "Candidate Instances": cnt,
                "Status": "Spatial Cluster Extracted" if cnt > 0 else "None in FOV",
            })
        st.table(pd.DataFrame(summary_rows))

    st.markdown("---")
    st.markdown("#### Candidate 3D Bounding Boxes Table")

    if len(clusters) > 0:
        box_rows = []
        for c in clusters:
            center_str = f"({c['center'][0]:.1f}, {c['center'][1]:.1f}, {c['center'][2]:.1f}) m"
            dims_str = f"{c['dims'][0]:.1f} × {c['dims'][1]:.1f} × {c['dims'][2]:.1f} m"
            box_rows.append({
                "ID": f"#{c['cluster_id']}",
                "Class": c["class_name"].capitalize(),
                "Points": c["point_count"],
                "Center (X, Y, Z)": center_str,
                "Dimensions (L×W×H)": dims_str,
            })
        st.dataframe(pd.DataFrame(box_rows), use_container_width=True)
    else:
        st.write("No dynamic or vulnerable object clusters detected above the spatial threshold.")
