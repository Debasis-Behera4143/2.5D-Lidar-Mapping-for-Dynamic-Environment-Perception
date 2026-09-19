"""
Metrics and comparative benchmark evaluation for uniform vs adaptive mapping.

Computes total cell counts, occupied spatial areas, points-per-cell density,
sparsity, analytical memory estimates, and percentage reductions.

NOTE: Memory estimates represent theoretical data-structure footprint models
(e.g. 64 bytes per cell record) rather than operating-system process heap profiling.
"""

from typing import Any, Dict, Optional

BYTES_PER_CELL_ESTIMATE = 64  # Baseline bytes per 2.5D cell record


def compute_map_summary(
    map_dict: Dict[str, Any],
    execution_time_s: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute quantitative summary statistics for a 2.5D grid map.

    Args:
        map_dict: Dictionary returned by uniform or adaptive grid mapper.
        execution_time_s: Optional measured execution time in seconds.

    Returns:
        Summary metrics dictionary.
    """
    cells = map_dict.get("cells", [])
    cell_count = int(map_dict.get("cell_count", len(cells)))
    point_count = int(map_dict.get("point_count", sum(c.get("point_count", 0) for c in cells)))

    # Coarse vs Fine cell counts
    coarse_count = int(map_dict.get(
        "coarse_cell_count",
        sum(1 for c in cells if c.get("level", "coarse") == "coarse")
    ))
    fine_count = int(map_dict.get(
        "fine_cell_count",
        sum(1 for c in cells if c.get("level") == "fine")
    ))

    # Occupied area in square meters
    occupied_area = 0.0
    res_dist: Dict[str, int] = {}
    for cell in cells:
        res = float(cell.get("resolution", 0.5))
        occupied_area += res * res
        res_key = f"{res:.2f}m"
        res_dist[res_key] = res_dist.get(res_key, 0) + 1

    avg_points_per_cell = float(point_count / cell_count) if cell_count > 0 else 0.0

    # Bounds area and sparsity
    bounds = map_dict.get("bounds", {})
    dx = max(0.0, float(bounds.get("max_x", 0.0) - bounds.get("min_x", 0.0)))
    dy = max(0.0, float(bounds.get("max_y", 0.0) - bounds.get("min_y", 0.0)))
    bounds_area = dx * dy
    if bounds_area > 0 and occupied_area > 0:
        sparsity = max(0.0, min(1.0, 1.0 - (occupied_area / bounds_area)))
    else:
        sparsity = 0.0

    # Analytical memory estimate
    estimated_mem_bytes = cell_count * BYTES_PER_CELL_ESTIMATE
    estimated_mem_kb = round(estimated_mem_bytes / 1024.0, 2)

    summary: Dict[str, Any] = {
        "map_type": str(map_dict.get("map_type", "unknown")),
        "cell_count": cell_count,
        "coarse_cell_count": coarse_count,
        "fine_cell_count": fine_count,
        "point_count": point_count,
        "occupied_area_m2": round(occupied_area, 2),
        "avg_points_per_cell": round(avg_points_per_cell, 2),
        "map_sparsity": round(sparsity, 4),
        "resolution_distribution": res_dist,
        "estimated_memory_bytes": estimated_mem_bytes,
        "estimated_memory_kb": estimated_mem_kb,
    }

    if execution_time_s is not None:
        summary["execution_time_ms"] = round(execution_time_s * 1000.0, 2)

    return summary


def compare_maps(
    uniform_map: Dict[str, Any],
    adaptive_map: Dict[str, Any],
    uniform_time_s: Optional[float] = None,
    adaptive_time_s: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compare uniform and adaptive 2.5D maps and compute efficiency metrics.

    Args:
        uniform_map: Result dictionary from UniformGridMapper.
        adaptive_map: Result dictionary from AdaptiveGridMapper.
        uniform_time_s: Optional execution time of uniform mapping in seconds.
        adaptive_time_s: Optional execution time of adaptive mapping in seconds.

    Returns:
        Dictionary containing uniform, adaptive, and comparative reduction percentages.
    """
    uni_summary = compute_map_summary(uniform_map, uniform_time_s)
    ada_summary = compute_map_summary(adaptive_map, adaptive_time_s)

    uni_cells = uni_summary["cell_count"]
    ada_cells = ada_summary["cell_count"]

    if uni_cells > 0:
        cell_reduction = ((uni_cells - ada_cells) / uni_cells) * 100.0
    else:
        cell_reduction = 0.0

    uni_mem = uni_summary["estimated_memory_bytes"]
    ada_mem = ada_summary["estimated_memory_bytes"]
    if uni_mem > 0:
        mem_reduction = ((uni_mem - ada_mem) / uni_mem) * 100.0
    else:
        mem_reduction = 0.0

    resolution_summary = {
        "uniform_resolution_m": uniform_map.get("resolution"),
        "adaptive_base_resolution_m": adaptive_map.get("base_resolution"),
        "adaptive_fine_resolution_m": adaptive_map.get("fine_resolution"),
        "coarse_cells": ada_summary["coarse_cell_count"],
        "fine_cells": ada_summary["fine_cell_count"],
    }

    comparison: Dict[str, Any] = {
        "cell_count_reduction_percent": round(cell_reduction, 2),
        "estimated_memory_reduction_percent": round(mem_reduction, 2),
        "resolution_summary": resolution_summary,
        "methodology_note": (
            "Memory estimates reflect a 64-byte analytical struct model per cell. "
            "Actual runtime heap consumption depends on runtime memory allocation."
        ),
    }

    return {
        "uniform": uni_summary,
        "adaptive": ada_summary,
        "comparison": comparison,
    }
