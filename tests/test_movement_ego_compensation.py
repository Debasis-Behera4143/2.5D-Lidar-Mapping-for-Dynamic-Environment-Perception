"""
Unit tests for Ego-Motion Compensation in LiDAR Movement Estimation.

Tests:
1. Identity / no-motion transformation.
2. Known translation and rotation compensation.
3. Preservation of static background points during ego-motion (avoiding false moving flags).
4. Detection of genuinely moving dynamic objects after ego-motion compensation.
5. Fallback behavior when pose information is missing or None.
"""

import numpy as np
import pytest

from src.mapping.config import MovementConfig
from src.mapping.movement import estimate_movement


def test_identity_pose_compensation():
    """Verify that identity poses produce identical results to uncompensated movement."""
    rng = np.random.default_rng(42)
    pts0 = rng.uniform(-20, 20, (500, 3)).astype(np.float32)
    # Small jitter within threshold (0.05m < 0.25m)
    pts1 = pts0 + rng.normal(0, 0.02, (500, 3)).astype(np.float32)

    pose_id = np.eye(4, dtype=np.float32)

    stats_uncomp, mask_uncomp = estimate_movement(pts1, pts0)
    stats_comp, mask_comp = estimate_movement(
        pts1, pts0, current_pose=pose_id, previous_pose=pose_id
    )

    assert stats_comp["ego_compensation_applied"] is True
    assert stats_comp["moving_point_count"] == stats_uncomp["moving_point_count"]
    np.testing.assert_array_equal(mask_comp, mask_uncomp)


def test_known_translation_compensation():
    """Verify static scene points are not marked moving when vehicle translates by 1.0m."""
    rng = np.random.default_rng(100)

    # Frame 0: 1000 static scene points in world coordinates
    world_pts = rng.uniform(-30, 30, (1000, 3)).astype(np.float32)

    # Pose 0: Sensor at origin (0, 0, 0)
    pose0 = np.eye(4, dtype=np.float32)
    pts0 = world_pts  # Sensor 0 sees world_pts directly

    # Pose 1: Sensor translates forward by +1.0m along X
    pose1 = np.eye(4, dtype=np.float32)
    pose1[0, 3] = 1.0  # tx = 1.0m

    # Sensor 1 sees points relative to its origin: X_sensor1 = X_world - 1.0m
    pts1 = world_pts.copy()
    pts1[:, 0] -= 1.0

    # WITHOUT compensation: direct local comparison sees 1.0m shift (> 0.25m)
    stats_no_comp, mask_no_comp = estimate_movement(
        pts1, pts0, config=MovementConfig(use_ego_compensation=False)
    )
    # WITHOUT compensation, static points appear displaced by 1.0m > 0.25m
    assert stats_no_comp["moving_point_ratio"] > 0.90

    # WITH compensation: transforms points into common world frame
    stats_comp, mask_comp = estimate_movement(
        pts1, pts0, current_pose=pose1, previous_pose=pose0
    )

    assert stats_comp["ego_compensation_applied"] is True
    # ALL static background points should be recognized as static (< 0.25m displacement)
    assert stats_comp["moving_point_count"] == 0
    assert stats_comp["moving_point_ratio"] == 0.0


def test_known_rotation_compensation():
    """Verify static scene points are not marked moving when vehicle rotates by 15 degrees yaw."""
    rng = np.random.default_rng(200)

    world_pts = rng.uniform(5, 25, (800, 3)).astype(np.float32)

    pose0 = np.eye(4, dtype=np.float32)
    pts0 = world_pts.copy()

    # Pose 1: Vehicle rotated 15 degrees around Z axis (yaw)
    angle = np.radians(15.0)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    R1 = np.array([
        [cos_a, -sin_a, 0.0],
        [sin_a,  cos_a, 0.0],
        [0.0,    0.0,   1.0],
    ], dtype=np.float32)

    pose1 = np.eye(4, dtype=np.float32)
    pose1[:3, :3] = R1

    # In sensor 1 frame: P_sensor1 = P_world @ R1
    pts1 = world_pts @ R1

    # WITHOUT compensation: high moving point ratio due to rotation
    stats_no_comp, _ = estimate_movement(
        pts1, pts0, config=MovementConfig(use_ego_compensation=False)
    )
    assert stats_no_comp["moving_point_ratio"] > 0.50

    # WITH compensation
    stats_comp, mask_comp = estimate_movement(
        pts1, pts0, current_pose=pose1, previous_pose=pose0
    )

    assert stats_comp["ego_compensation_applied"] is True
    assert stats_comp["moving_point_count"] == 0


def test_genuinely_moving_object_detected_after_compensation():
    """Verify genuinely moving objects (moving vehicle) are still detected after ego-motion compensation."""
    rng = np.random.default_rng(300)

    # 500 static background points
    static_world = rng.uniform(-20, 20, (500, 3)).astype(np.float32)

    # 100 points belonging to a moving car
    car_world_t0 = rng.uniform(5, 8, (100, 3)).astype(np.float32)
    # Car moves 1.5m along Y between frame 0 and frame 1
    car_world_t1 = car_world_t0.copy()
    car_world_t1[:, 1] += 1.5  # 1.5m displacement (> 0.25m)

    # Ego vehicle translates +1.0m along X
    pose0 = np.eye(4, dtype=np.float32)
    pose1 = np.eye(4, dtype=np.float32)
    pose1[0, 3] = 1.0

    # Frame 0 points in sensor 0 frame
    pts0 = np.vstack([static_world, car_world_t0])

    # Frame 1 points in sensor 1 frame
    static_s1 = static_world.copy()
    static_s1[:, 0] -= 1.0  # Ego motion offset
    car_s1 = car_world_t1.copy()
    car_s1[:, 0] -= 1.0     # Ego motion offset

    pts1 = np.vstack([static_s1, car_s1])

    stats_comp, mask_comp = estimate_movement(
        pts1, pts0, current_pose=pose1, previous_pose=pose0
    )

    assert stats_comp["ego_compensation_applied"] is True
    # Static points (first 500) should NOT be moving
    assert np.sum(mask_comp[:500]) == 0
    # Moving car points (last 100) SHOULD be detected as moving (> 0.25m displacement)
    assert np.sum(mask_comp[500:]) >= 90


def test_missing_pose_fallback():
    """Verify graceful degradation when pose parameters are None."""
    rng = np.random.default_rng(400)
    pts0 = rng.uniform(-10, 10, (200, 3)).astype(np.float32)
    pts1 = pts0 + 0.05  # within 0.25m threshold

    # None passed for poses
    stats, mask = estimate_movement(pts1, pts0, current_pose=None, previous_pose=None)

    assert stats["available"] is True
    assert stats["ego_compensation_applied"] is False
    assert stats["moving_point_count"] == 0
