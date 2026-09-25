"""
3D Instance Clustering and Spatial Object Perception Engine.

Transforms semantic point cloud classifications into discrete 3D instances
with bounding boxes, ego-centric spatial positions, distances, and forward
field-of-view obstacle analysis.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from sklearn.cluster import DBSCAN
    _HAS_SKLEARN = True
except (ImportError, OSError):
    _HAS_SKLEARN = False


def _scipy_dbscan(points: np.ndarray, eps: float, min_samples: int) -> np.ndarray:
    """Fast spatial clustering fallback using SciPy cKDTree when sklearn DLLs are blocked."""
    from scipy.spatial import cKDTree
    tree = cKDTree(points)
    neighbors_list = tree.query_ball_tree(tree, eps)

    n = len(points)
    labels = np.full(n, -1, dtype=int)
    cluster_id = 0

    for i in range(n):
        if labels[i] != -1:
            continue
        neighbors = neighbors_list[i]
        if len(neighbors) < min_samples:
            continue
        labels[i] = cluster_id
        queue = list(neighbors)
        head = 0
        while head < len(queue):
            q_pt = queue[head]
            head += 1
            if labels[q_pt] == -1:
                labels[q_pt] = cluster_id
                q_neighbors = neighbors_list[q_pt]
                if len(q_neighbors) >= min_samples:
                    queue.extend(q_neighbors)
        cluster_id += 1

    return labels


from src.ai.label_mapping import ID_TO_CLASS


def compute_relative_sector(x: float, y: float) -> str:
    """
    Determine ego-centric angular sector relative to the vehicle heading (X-axis forward, Y-axis left).
    """
    angle_deg = np.degrees(np.arctan2(y, x))  # [-180, 180], 0 is straight ahead, +90 is left, -90 is right

    if -22.5 <= angle_deg <= 22.5:
        return "FRONT"
    elif 22.5 < angle_deg <= 67.5:
        return "FRONT-LEFT"
    elif 67.5 < angle_deg <= 112.5:
        return "LEFT"
    elif 112.5 < angle_deg <= 157.5:
        return "REAR-LEFT"
    elif angle_deg > 157.5 or angle_deg < -157.5:
        return "REAR"
    elif -157.5 <= angle_deg < -112.5:
        return "REAR-RIGHT"
    elif -112.5 <= angle_deg < -67.5:
        return "RIGHT"
    else:  # -67.5 <= angle_deg < -22.5
        return "FRONT-RIGHT"


class InstancePerceptionEngine:
    """
    Clusters semantic points into discrete 3D object instances and calculates
    geometric bounding boxes, ranges, and forward obstacle sectors.
    """

    CLUSTER_PARAMS = {
        4: {"name": "vehicle", "eps": 2.2, "min_samples": 4, "min_points": 6},
        5: {"name": "pedestrian", "eps": 1.0, "min_samples": 3, "min_points": 4},
        6: {"name": "pole_sign", "eps": 1.0, "min_samples": 3, "min_points": 4},
        3: {"name": "vegetation", "eps": 3.0, "min_samples": 6, "min_points": 8},
        2: {"name": "building", "eps": 4.0, "min_samples": 8, "min_points": 12},
    }

    @classmethod
    def extract_instances(
        cls,
        points: np.ndarray,
        labels: np.ndarray,
        confidences: Optional[np.ndarray] = None,
        frame_id: str = "000000",
        front_angle_deg: float = 30.0,
        front_range_m: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Extract 3D object instances from classified LiDAR points.

        Args:
            points: (N, 3) or (N, 4) coordinates [X forward, Y left, Z height].
            labels: (N,) predicted semantic class IDs (0-7).
            confidences: (N,) confidence scores.
            frame_id: Frame identifier string.
            front_angle_deg: Half-angle for forward cone of interest (default 30 deg).
            front_range_m: Max range for forward obstacle consideration (default 60 m).

        Returns:
            Dictionary containing detected objects, front objects, scene summary, and proximity status.
        """
        pts = np.asarray(points)[:, :3]
        lbls = np.asarray(labels)
        confs = np.asarray(confidences) if confidences is not None else np.ones(len(pts), dtype=np.float32)

        objects: List[Dict[str, Any]] = []
        front_objects: List[Dict[str, Any]] = []
        obj_id_counter = 1

        # Track counts for summary
        class_instance_counts: Dict[str, int] = {
            "vehicles": 0,
            "pedestrians": 0,
            "poles_signs": 0,
            "vegetation_clusters": 0,
            "buildings": 0,
        }

        # Cluster dynamic and discrete classes
        for class_id, params in cls.CLUSTER_PARAMS.items():
            mask = lbls == class_id
            if not np.any(mask):
                continue

            class_pts = pts[mask]
            class_confs = confs[mask]

            if len(class_pts) < params["min_points"]:
                continue

            # Run DBSCAN spatial clustering (with fast SciPy fallback if sklearn DLL blocked)
            if _HAS_SKLEARN:
                db = DBSCAN(eps=params["eps"], min_samples=params["min_samples"]).fit(class_pts)
                cluster_labels = db.labels_
            else:
                cluster_labels = _scipy_dbscan(class_pts, eps=params["eps"], min_samples=params["min_samples"])

            unique_clusters = set(cluster_labels)
            if -1 in unique_clusters:
                unique_clusters.remove(-1)  # Ignore noise points

            for cluster_id in sorted(unique_clusters):
                c_mask = cluster_labels == cluster_id
                c_pts = class_pts[c_mask]
                c_confs = class_confs[c_mask]

                if len(c_pts) < params["min_points"]:
                    continue

                min_x, max_x = float(np.min(c_pts[:, 0])), float(np.max(c_pts[:, 0]))
                min_y, max_y = float(np.min(c_pts[:, 1])), float(np.max(c_pts[:, 1]))
                min_z, max_z = float(np.min(c_pts[:, 2])), float(np.max(c_pts[:, 2]))

                center_x = round((min_x + max_x) / 2.0, 3)
                center_y = round((min_y + max_y) / 2.0, 3)
                center_z = round((min_z + max_z) / 2.0, 3)

                dx = round(max(0.2, max_x - min_x), 3)  # length
                dy = round(max(0.2, max_y - min_y), 3)  # width
                dz = round(max(0.2, max_z - min_z), 3)  # height

                # Skip unrealistically large single clusters for discrete vehicles/pedestrians
                if class_id == 4 and (dx > 18.0 or dy > 8.0):
                    continue
                if class_id == 5 and (dx > 3.0 or dy > 3.0 or dz > 2.5):
                    continue

                distance_3d = round(float(np.sqrt(center_x**2 + center_y**2 + center_z**2)), 2)
                distance_2d = round(float(np.sqrt(center_x**2 + center_y**2)), 2)
                mean_conf = round(float(np.mean(c_confs)), 3)
                position_sector = compute_relative_sector(center_x, center_y)

                # Check if object is in front of ego vehicle (X > 0 and within front angle cone)
                angle_deg = np.degrees(np.arctan2(center_y, center_x))
                is_front = (center_x > 0.5) and (abs(angle_deg) <= front_angle_deg) and (distance_2d <= front_range_m)

                class_name = ID_TO_CLASS.get(class_id, params["name"])

                obj_record = {
                    "id": obj_id_counter,
                    "class_id": int(class_id),
                    "class_name": class_name,
                    "confidence": mean_conf,
                    "point_count": int(len(c_pts)),
                    "center": {
                        "x": center_x,
                        "y": center_y,
                        "z": center_z,
                    },
                    "size": {
                        "length": dx,
                        "width": dy,
                        "height": dz,
                    },
                    "bounds": {
                        "min_x": round(min_x, 3),
                        "max_x": round(max_x, 3),
                        "min_y": round(min_y, 3),
                        "max_y": round(max_y, 3),
                        "min_z": round(min_z, 3),
                        "max_z": round(max_z, 3),
                    },
                    "distance_m": distance_3d,
                    "horizontal_distance_m": distance_2d,
                    "position": position_sector,
                    "is_in_front": bool(is_front),
                }

                objects.append(obj_record)
                if is_front:
                    front_objects.append(obj_record)

                # Count by category
                if class_id == 4:
                    class_instance_counts["vehicles"] += 1
                elif class_id == 5:
                    class_instance_counts["pedestrians"] += 1
                elif class_id == 6:
                    class_instance_counts["poles_signs"] += 1
                elif class_id == 3:
                    class_instance_counts["vegetation_clusters"] += 1
                elif class_id == 2:
                    class_instance_counts["buildings"] += 1

                obj_id_counter += 1

        # Sort objects by distance
        objects.sort(key=lambda o: o["distance_m"])
        front_objects.sort(key=lambda o: o["distance_m"])

        nearest_front = front_objects[0] if front_objects else None
        nearest_overall = objects[0] if objects else None

        # Determine Proximity Status
        if nearest_front:
            min_d = nearest_front["distance_m"]
            if min_d < 5.0:
                proximity_status = {"level": "VERY CLOSE", "color": "#ef4444", "distance_m": min_d, "nearest_object": nearest_front}
            elif min_d < 14.0:
                proximity_status = {"level": "CAUTION", "color": "#f59e0b", "distance_m": min_d, "nearest_object": nearest_front}
            else:
                proximity_status = {"level": "SAFE", "color": "#10b981", "distance_m": min_d, "nearest_object": nearest_front}
        else:
            proximity_status = {"level": "CLEAR", "color": "#10b981", "distance_m": None, "nearest_object": None}

        scene_summary = {
            "total_instances_detected": len(objects),
            "vehicles_count": class_instance_counts["vehicles"],
            "pedestrians_count": class_instance_counts["pedestrians"],
            "poles_signs_count": class_instance_counts["poles_signs"],
            "vegetation_regions": class_instance_counts["vegetation_clusters"],
            "building_structures": class_instance_counts["buildings"],
            "drivable_road_detected": bool(np.any(lbls == 0)),
            "sidewalk_detected": bool(np.any(lbls == 1)),
            "nearest_obstacle": nearest_overall,
        }

        return {
            "_success": True,
            "frame_id": frame_id,
            "total_points": len(pts),
            "objects": objects,
            "front_objects": front_objects,
            "proximity_status": proximity_status,
            "scene_summary": scene_summary,
        }
