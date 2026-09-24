"""
High-Fidelity Deterministic Simulation Data Provider.

Generates realistic 3D LiDAR point clouds, semantic segmentations,
adaptive multi-resolution grid maps, side/front elevation maps,
elevation profiles, object statistics, system logs, and performance metrics
for interactive perception demonstration without requiring a live backend or GPU.

All metrics and counts produced by this provider are clearly labeled internally
and presentationally as SIMULATION.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np

from src.frontend.config import (
    CLASS_COLORS,
    CLASS_NAMES,
    DISPLAY_CLASS_COLORS,
    DISPLAY_CLASS_NAMES,
)
from src.frontend.providers.base_provider import BaseDataProvider


class SimulationDataProvider(BaseDataProvider):
    """
    Generates rich, deterministic, spatial LiDAR simulation data.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._cached_scenes: Dict[str, Dict[str, Any]] = {}

    def get_source_type(self) -> str:
        return "Simulation"

    def check_health(self) -> Dict[str, Any]:
        return {
            "online": True,
            "status": "simulation_ready",
            "provider": "SimulationEngine (Deterministic)",
            "ping_ms": 0.5,
            "device": "Local Engine",
            "mode": "Simulation Mode",
        }

    def get_available_frames(self) -> List[Dict[str, Any]]:
        return [
            {
                "frame_id": "1248",
                "sample_id": "sim_urban_1248",
                "dataset_type": "nuScenes (LiDAR)",
                "sequence_id": "scene-0061",
                "point_count": 1284365,
                "description": "Urban Multi-Lane Boulevard with Dynamic Traffic & Pedestrians",
                "has_ground_truth": True,
            },
            {
                "frame_id": "1249",
                "sample_id": "sim_urban_1249",
                "dataset_type": "SemanticKITTI Demo",
                "sequence_id": "00",
                "point_count": 1312500,
                "description": "Signalized Intersection with Crossing Pedestrians",
                "has_ground_truth": True,
            },
            {
                "frame_id": "1250",
                "sample_id": "sim_urban_1250",
                "dataset_type": "nuScenes (LiDAR)",
                "sequence_id": "scene-0062",
                "point_count": 1258900,
                "description": "Arterial Road with Overhead Structure & Terrain Slope",
                "has_ground_truth": True,
            },
        ]

    def get_perception_data(self, frame_id: str = "1248", **kwargs) -> Dict[str, Any]:
        """
        Generate a complete 3D LiDAR perception scene with realistic road,
        sidewalk, vehicles, trees, buildings, pedestrians, and street furniture.
        """
        if frame_id in self._cached_scenes:
            return self._cached_scenes[frame_id]

        rng = np.random.RandomState(int(frame_id) if frame_id.isdigit() else 1248)

        points_list: List[List[float]] = []
        labels_list: List[int] = []
        confs_list: List[float] = []

        # 1. Drivable Road (Class 0, Blue #2563eb)
        # Multi-lane road: X from -12m to 55m, Y from -4.2m to 4.2m
        n_road = 1800
        rx = rng.uniform(-12.0, 55.0, n_road)
        ry = rng.uniform(-4.2, 4.2, n_road)
        # Subtle crown: slightly higher at center (0.05m)
        rz = 0.05 - 0.003 * (ry ** 2) + rng.normal(0, 0.015, n_road)
        r_int = rng.uniform(0.15, 0.45, n_road)
        for x, y, z, it in zip(rx, ry, rz, r_int):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), round(float(it), 3)])
            labels_list.append(0)
            confs_list.append(round(float(rng.uniform(0.95, 0.99)), 3))

        # 2. Sidewalks (Class 1, Violet #8b5cf6)
        # Left sidewalk (Y: -6.2 to -4.2), Right sidewalk (Y: 4.2 to 6.2)
        n_side = 500
        sx_l = rng.uniform(-12.0, 55.0, n_side // 2)
        sy_l = rng.uniform(-6.2, -4.2, n_side // 2)
        sz_l = rng.uniform(0.15, 0.22, n_side // 2)

        sx_r = rng.uniform(-12.0, 55.0, n_side // 2)
        sy_r = rng.uniform(4.2, 6.2, n_side // 2)
        sz_r = rng.uniform(0.15, 0.22, n_side // 2)

        sx = np.concatenate([sx_l, sx_r])
        sy = np.concatenate([sy_l, sy_r])
        sz = np.concatenate([sz_l, sz_r])
        s_int = rng.uniform(0.2, 0.5, n_side)
        for x, y, z, it in zip(sx, sy, sz, s_int):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), round(float(it), 3)])
            labels_list.append(1)
            confs_list.append(round(float(rng.uniform(0.92, 0.98)), 3))

        # 3. Building / Wall (Class 2, Red #ef4444)
        # Along left perimeter: Y from -9.5m to -6.2m, height Z up to 3.8m
        n_bld = 850
        bx = rng.uniform(-10.0, 50.0, n_bld)
        # Dense facade at Y=-6.4m to -8.5m
        by = rng.uniform(-8.5, -6.4, n_bld)
        bz = rng.uniform(0.2, 3.8, n_bld)
        b_int = rng.uniform(0.4, 0.85, n_bld)
        for x, y, z, it in zip(bx, by, bz, b_int):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), round(float(it), 3)])
            labels_list.append(2)
            confs_list.append(round(float(rng.uniform(0.93, 0.99)), 3))

        # 4. Vegetation / Trees (Class 3, Green #10b981)
        # Along right side (Y: 6.2 to 10.5m), clustered around tree trunks
        tree_centers = [(8.0, 7.5), (22.0, 8.0), (36.0, 7.8), (48.0, 8.2)]
        for tx, ty in tree_centers:
            # Trunk
            n_trunk = 50
            tk_z = rng.uniform(0.2, 2.2, n_trunk)
            tk_x = tx + rng.normal(0, 0.18, n_trunk)
            tk_y = ty + rng.normal(0, 0.18, n_trunk)
            for x, y, z in zip(tk_x, tk_y, tk_z):
                points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.3])
                labels_list.append(3)
                confs_list.append(0.95)
            # Foliage crown (lush sphere)
            n_crown = 220
            phi = rng.uniform(0, 2 * np.pi, n_crown)
            costheta = rng.uniform(-1, 1, n_crown)
            u = rng.uniform(0, 1, n_crown)
            r = 2.2 * (u ** (1 / 3))
            theta = np.arccos(costheta)
            cr_x = tx + r * np.sin(theta) * np.cos(phi)
            cr_y = ty + r * np.sin(theta) * np.sin(phi)
            cr_z = 4.2 + (r * np.cos(theta) * 0.9)
            for x, y, z in zip(cr_x, cr_y, cr_z):
                points_list.append([round(float(x), 3), round(float(y), 3), max(0.5, round(float(z), 3)), 0.65])
                labels_list.append(3)
                confs_list.append(round(float(rng.uniform(0.91, 0.98)), 3))

        # 5. Vehicles (Class 4, Magenta #d946ef)
        # Leading vehicles: Car 1 (X=15.5m), Car 2 (X=28.5m), Car 3 (X=41.0m)
        car_configs = [
            {"cx": 15.5, "cy": 0.4, "dx": 4.5, "dy": 1.9, "dz": 1.45, "points": 180},
            {"cx": 28.5, "cy": -1.8, "dx": 4.6, "dy": 2.0, "dz": 1.55, "points": 160},
            {"cx": 41.0, "cy": 1.2, "dx": 4.4, "dy": 1.9, "dz": 1.40, "points": 120},
        ]
        for car in car_configs:
            cx, cy = car["cx"], car["cy"]
            dx, dy, dz = car["dx"], car["dy"], car["dz"]
            n_car = car["points"]
            # Exterior surface shell
            vx = cx + rng.uniform(-dx / 2, dx / 2, n_car)
            vy = cy + rng.uniform(-dy / 2, dy / 2, n_car)
            vz = rng.uniform(0.1, dz, n_car)
            v_int = rng.uniform(0.6, 0.95, n_car)
            for x, y, z, it in zip(vx, vy, vz, v_int):
                points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), round(float(it), 3)])
                labels_list.append(4)
                confs_list.append(round(float(rng.uniform(0.94, 0.99)), 3))

        # Ego Vehicle at (0, 0)
        n_ego = 140
        ex = rng.uniform(-2.2, 2.2, n_ego)
        ey = rng.uniform(-0.95, 0.95, n_ego)
        ez = rng.uniform(0.1, 1.45, n_ego)
        for x, y, z in zip(ex, ey, ez):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.85])
            labels_list.append(4)
            confs_list.append(0.99)

        # 6. Pedestrians (Class 5, Yellow #eab308)
        ped_configs = [
            {"cx": 13.5, "cy": 5.1, "points": 60, "height": 1.72},
            {"cx": 24.0, "cy": 5.4, "points": 50, "height": 1.68},
        ]
        for ped in ped_configs:
            px, py = ped["cx"], ped["cy"]
            h = ped["height"]
            n_ped = ped["points"]
            p_x = px + rng.normal(0, 0.22, n_ped)
            p_y = py + rng.normal(0, 0.22, n_ped)
            p_z = rng.uniform(0.2, h, n_ped)
            for x, y, z in zip(p_x, p_y, p_z):
                points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.5])
                labels_list.append(5)
                confs_list.append(round(float(rng.uniform(0.89, 0.97)), 3))

        # 7. Poles / Signs (Class 6, Cyan #06b6d4)
        poles = [(6.0, 5.8, 3.8), (20.0, 5.8, 4.0), (34.0, 5.8, 4.2), (18.0, -6.3, 3.0)]
        for pl_x, pl_y, pl_z in poles:
            n_pl = 45
            pz = rng.uniform(0.2, pl_z, n_pl)
            px = pl_x + rng.normal(0, 0.08, n_pl)
            py = pl_y + rng.normal(0, 0.08, n_pl)
            for x, y, z in zip(px, py, pz):
                points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.7])
                labels_list.append(6)
                confs_list.append(0.94)

        # 8. Ground / Terrain (Class 7, Orange #f97316)
        # Background terrain beyond right sidewalk (Y: 9.5m to 16.0m)
        n_grd = 300
        gx = rng.uniform(-10.0, 50.0, n_grd)
        gy = rng.uniform(9.5, 16.0, n_grd)
        gz = 0.15 + 0.02 * (gy - 9.5) + rng.normal(0, 0.05, n_grd)
        for x, y, z in zip(gx, gy, gz):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.3])
            labels_list.append(7)
            confs_list.append(0.96)

        # 9. Barrier (Class 8, Brown #b45309)
        n_bar = 120
        bx = rng.uniform(-8.0, 45.0, n_bar)
        by = -6.3 + rng.normal(0, 0.06, n_bar)
        bz = rng.uniform(0.15, 0.75, n_bar)
        for x, y, z in zip(bx, by, bz):
            points_list.append([round(float(x), 3), round(float(y), 3), round(float(z), 3), 0.6])
            labels_list.append(8)
            confs_list.append(0.93)

        # Calculate class distribution
        class_dist: Dict[str, int] = {}
        for lbl in labels_list:
            name = CLASS_NAMES.get(lbl, f"class_{lbl}")
            class_dist[name] = class_dist.get(name, 0) + 1

        # Annotations exactly matching reference image
        annotations = [
            {
                "id": "wall",
                "title": "Wall (Non-drivable)",
                "subtext": "Height: ~2.5 m",
                "color": "#ef4444",
                "world_pos": [-6.8, 12.0, 2.5],
            },
            {
                "id": "vehicle",
                "title": "Vehicle (Dynamic)",
                "subtext": "Height: ~1.5 m",
                "color": "#d946ef",
                "world_pos": [0.4, 15.5, 1.5],
            },
            {
                "id": "tree",
                "title": "Tree (Static)",
                "subtext": "Height: ~5 m",
                "color": "#10b981",
                "world_pos": [7.8, 22.0, 4.8],
            },
            {
                "id": "pedestrian",
                "title": "Pedestrian (Dynamic)",
                "subtext": "Height: ~1.7 m",
                "color": "#eab308",
                "world_pos": [5.2, 13.5, 1.7],
            },
            {
                "id": "road",
                "title": "Drivable Road",
                "subtext": "Height: ~0.0–0.5 m",
                "color": "#00d4ff",
                "world_pos": [0.0, 4.0, 0.05],
            },
        ]

        result = {
            "_success": True,
            "provenance": "SIMULATION",
            "frame_id": frame_id,
            "dataset": "nuScenes (LiDAR) / SemanticKITTI Demo",
            "total_points": 1284365,
            "downsampled_points": len(points_list),
            "points": points_list,
            "predicted_labels": labels_list,
            "confidence_scores": confs_list,
            "class_distribution": class_dist,
            "confidence_information": {
                "mean": round(float(np.mean(confs_list)), 3),
                "min": round(float(np.min(confs_list)), 3),
                "max": round(float(np.max(confs_list)), 3),
                "std": round(float(np.std(confs_list)), 3),
            },
            "annotations": annotations,
            "timestamp": "14:32:17",
        }

        self._cached_scenes[frame_id] = result
        return result

    def get_adaptive_map(
        self,
        perception_payload: Dict[str, Any],
        base_resolution: float = 0.50,
        fine_resolution: float = 0.05,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate quadtree-style variable-resolution grid cells:
        - 5 cm (0.05m): Critical near-field (0-10m) & dynamic obstacles (vehicles, pedestrians)
        - 10 cm (0.10m): Mid-field corridor (10-25m) & sidewalks
        - 25 cm (0.25m): Static obstacles & structures (25-50m)
        - 50 cm (0.50m): Far background terrain (50-100m)
        """
        cells: List[Dict[str, Any]] = []

        # Road & Ego vehicle near region: High resolution (0.05m - 0.10m)
        for x in np.arange(-5.0, 20.0, 0.5):
            for y in np.arange(-3.5, 3.5, 0.5):
                dist = np.hypot(x, y)
                res = 0.05 if dist < 12.0 else 0.10
                level = "fine" if res <= 0.10 else "medium"
                cells.append({
                    "center_x": round(float(x), 2),
                    "center_y": round(float(y), 2),
                    "resolution": res,
                    "level": level,
                    "mean_height": 0.05,
                    "max_height": 0.10,
                    "min_height": 0.00,
                    "point_count": int(res * 240),
                    "dominant_class": 0,
                    "importance_score": round(max(0.75, 1.0 - (dist / 60.0)), 2),
                    "is_dynamic": False,
                })

        # Dynamic vehicles region: fine cells (0.05m)
        dynamic_locs = [(15.5, 0.4, 4, 1.45), (28.5, -1.8, 4, 1.55), (41.0, 1.2, 4, 1.40)]
        for vx, vy, cls_id, h in dynamic_locs:
            for dx in np.arange(-2.5, 2.5, 0.4):
                for dy in np.arange(-1.2, 1.2, 0.4):
                    cells.append({
                        "center_x": round(float(vx + dx), 2),
                        "center_y": round(float(vy + dy), 2),
                        "resolution": 0.05,
                        "level": "fine",
                        "mean_height": round(float(h), 2),
                        "max_height": round(float(h + 0.1), 2),
                        "min_height": 0.1,
                        "point_count": 85,
                        "dominant_class": cls_id,
                        "importance_score": 0.98,
                        "is_dynamic": True,
                    })

        # Pedestrians region: ultra-fine cells (0.05m)
        ped_locs = [(13.5, 5.1), (24.0, 5.4)]
        for px, py in ped_locs:
            for dx in [-0.25, 0.25]:
                for dy in [-0.25, 0.25]:
                    cells.append({
                        "center_x": round(float(px + dx), 2),
                        "center_y": round(float(py + dy), 2),
                        "resolution": 0.05,
                        "level": "fine",
                        "mean_height": 1.7,
                        "max_height": 1.75,
                        "min_height": 0.2,
                        "point_count": 45,
                        "dominant_class": 5,
                        "importance_score": 0.99,
                        "is_dynamic": True,
                    })

        # Sidewalks: medium resolution (0.10m - 0.25m)
        for x in np.arange(-5.0, 45.0, 1.0):
            for y in [-5.2, 5.2]:
                cells.append({
                    "center_x": round(float(x), 2),
                    "center_y": round(float(y), 2),
                    "resolution": 0.10,
                    "level": "medium",
                    "mean_height": 0.18,
                    "max_height": 0.22,
                    "min_height": 0.15,
                    "point_count": 42,
                    "dominant_class": 1,
                    "importance_score": 0.65,
                    "is_dynamic": False,
                })

        # Buildings / Walls (left): coarse-to-medium (0.25m - 0.50m)
        for x in np.arange(-5.0, 45.0, 2.0):
            for y in [-7.5, -9.0]:
                cells.append({
                    "center_x": round(float(x), 2),
                    "center_y": round(float(y), 2),
                    "resolution": 0.25,
                    "level": "coarse",
                    "mean_height": 2.5,
                    "max_height": 3.8,
                    "min_height": 0.2,
                    "point_count": 64,
                    "dominant_class": 2,
                    "importance_score": 0.45,
                    "is_dynamic": False,
                })

        # Trees & Far Terrain (right): coarse resolution (0.50m)
        for x in np.arange(0.0, 50.0, 3.0):
            for y in [8.5, 12.0]:
                cells.append({
                    "center_x": round(float(x), 2),
                    "center_y": round(float(y), 2),
                    "resolution": 0.50,
                    "level": "coarse",
                    "mean_height": 4.5 if y < 10 else 0.3,
                    "max_height": 5.2 if y < 10 else 0.4,
                    "min_height": 0.1,
                    "point_count": 55,
                    "dominant_class": 3 if y < 10 else 7,
                    "importance_score": 0.35,
                    "is_dynamic": False,
                })

        return {
            "_success": True,
            "provenance": "SIMULATION",
            "map_type": "adaptive_variable_resolution",
            "cell_count": len(cells),
            "simulated_full_cell_count": 8420,
            "cells": cells,
            "base_resolution": base_resolution,
            "fine_resolution": fine_resolution,
            "bounds": {"min_x": -10.0, "max_x": 55.0, "min_y": -10.0, "max_y": 14.0},
        }

    def get_uniform_map(
        self,
        perception_payload: Dict[str, Any],
        resolution: float = 0.05,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate uniform 5 cm grid representation for baseline comparison.
        """
        cells: List[Dict[str, Any]] = []
        for x in np.arange(-5.0, 35.0, 1.2):
            for y in np.arange(-8.0, 10.0, 1.2):
                cells.append({
                    "center_x": round(float(x), 2),
                    "center_y": round(float(y), 2),
                    "resolution": resolution,
                    "level": "uniform_fixed",
                    "mean_height": 0.15,
                    "point_count": 30,
                    "dominant_class": 0 if abs(y) < 4.0 else (2 if y < -5 else (3 if y > 6 else 1)),
                    "importance_score": 0.5,
                    "is_dynamic": False,
                })
        return {
            "_success": True,
            "provenance": "SIMULATION",
            "map_type": "uniform_fixed_resolution",
            "resolution": resolution,
            "cell_count": 26400,  # Simulated realistic full uniform count
            "cells": cells,
        }

    def get_map_comparison(
        self,
        uniform_map: Dict[str, Any],
        adaptive_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "_success": True,
            "provenance": "SIMULATION",
            "comparison": {
                "uniform_cells": 26400,
                "adaptive_cells": 8420,
                "cell_count_reduction_percent": -68.1,
                "memory_uniform_kb": 1690.0,
                "memory_adaptive_kb": 538.9,
                "memory_reduction_percent": -68.1,
                "uniform_runtime_ms": 175.0,
                "adaptive_runtime_ms": 55.0,
                "speedup_factor": 3.18,
                "coverage_area_m2": 1560.0,
            },
        }

    def get_elevation_profile(self, frame_id: str = "1248") -> Dict[str, Any]:
        """
        Generate continuous 1D elevation contour matching reference image:
        Distance (m) 0-100m on X, Height (m) 0-10m on Y.
        """
        x_dist = np.linspace(0.0, 100.0, 200)
        # Base road/terrain elevation with dynamic vehicles, gentle slopes,
        # and elevation peak (~7.8m at distance ~60m)
        y_height = (
            0.2
            + 0.8 * np.exp(-0.5 * ((x_dist - 16.0) / 3.0) ** 2)  # Vehicle 1 bump
            + 1.6 * np.exp(-0.5 * ((x_dist - 28.0) / 6.0) ** 2)  # Structure / tree
            + 6.8 * np.exp(-0.5 * ((x_dist - 62.0) / 10.0) ** 2)  # Overpass / high hill peak
            + 1.2 * np.exp(-0.5 * ((x_dist - 94.0) / 5.0) ** 2)  # Far incline
            + 0.05 * np.sin(x_dist * 0.2)
        )
        return {
            "provenance": "SIMULATION",
            "distance_m": [round(float(d), 2) for d in x_dist],
            "height_m": [max(0.0, round(float(h), 2)) for h in y_height],
            "max_height_m": round(float(np.max(y_height)), 2),
            "min_height_m": 0.0,
        }

    def get_performance_metrics(self, frame_id: str = "1248") -> Dict[str, Any]:
        return {
            "provenance": "SIMULATION",
            "miou_percent": 87.0,
            "miou_badge": "SIMULATION",
            "fps": 18.0,
            "fps_badge": "SIMULATION",
            "latency_ms": 55.0,
            "latency_badge": "SIMULATION",
            "memory_mb": 820.0,
            "memory_badge": "SIMULATION",
        }

    def get_system_logs(self, frame_id: str = "1248") -> List[Dict[str, str]]:
        return [
            {"time": "14:32:10", "tag": "INFO", "msg": f"Loaded frame {frame_id}"},
            {"time": "14:32:11", "tag": "INFO", "msg": "Point cloud: 1,284,365 points ingested"},
            {"time": "14:32:13", "tag": "SUCCESS", "msg": "AI semantic segmentation completed (RandLA-Net)"},
            {"time": "14:32:15", "tag": "SUCCESS", "msg": "Adaptive grid generated (5cm / 10cm / 25cm / 50cm)"},
            {"time": "14:32:16", "tag": "SUCCESS", "msg": "2.5D elevation map updated"},
            {"time": "14:32:17", "tag": "READY", "msg": "Ready (18 FPS, 55 ms latency)"},
        ]

    def get_scene_objects(self, frame_id: str = "1248") -> Dict[str, int]:
        return {
            "Vehicle": 3,
            "Pedestrian": 2,
            "Motorcycle": 0,
            "Bicycle": 1,
            "Static (Pole/Sign)": 4,
            "Others": 1,
        }

    def get_annotations(self, frame_id: str = "1248") -> List[Dict[str, Any]]:
        perc = self.get_perception_data(frame_id)
        return perc.get("annotations", [])
