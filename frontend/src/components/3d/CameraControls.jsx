/**
 * CameraControls.jsx
 * Multi-perspective camera controller supporting:
 * - 3D Orbit (Perspective)
 * - Top (Bird's Eye View / BEV)
 * - Front (Driver forward view)
 * - Side (Elevation profile view)
 * - Ego POV (Sensor coordinate center)
 * - Fit (Scene framing)
 */

import React, { useEffect, useRef } from 'react';
import { useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

export default function CameraControls({
  viewMode = 'orbit',
  bounds = null,
  sensorPosition = [0, 0, 0],
}) {
  const controlsRef = useRef();
  const { camera } = useThree();

  useEffect(() => {
    if (!controlsRef.current) return;

    const sx = sensorPosition[0] || 0;
    const sy = sensorPosition[1] || 0;
    const sz = sensorPosition[2] || 0;

    if (viewMode === 'bev' || viewMode === 'top') {
      // Top-Down Bird's Eye View looking straight down
      camera.position.set(sx, sy + 55, sz + 0.01);
      controlsRef.current.target.set(sx, sy, sz - 10);
    } else if (viewMode === 'front') {
      // Front view looking toward oncoming scan
      camera.position.set(sx, sy + 4.0, sz - 45);
      controlsRef.current.target.set(sx, sy, sz - 10);
    } else if (viewMode === 'side') {
      // Side view looking at longitudinal profile
      camera.position.set(sx + 45, sy + 6.0, sz - 10);
      controlsRef.current.target.set(sx, sy, sz - 10);
    } else if (viewMode === 'ego') {
      // Ego Vehicle / Sensor POV
      camera.position.set(sx, sy + 1.8, sz + 1.0);
      controlsRef.current.target.set(sx, sy + 1.0, sz - 35);
    } else if (viewMode === 'fit') {
      // Framing entire bounding envelope
      if (bounds) {
        const midX = -((bounds.min_y + bounds.max_y) / 2 || 0);
        const midY = (bounds.min_z + bounds.max_z) / 2 || 0;
        const midZ = -((bounds.min_x + bounds.max_x) / 2 || 10);
        const span = Math.max(
          bounds.max_x - bounds.min_x || 40,
          bounds.max_y - bounds.min_y || 40
        );
        camera.position.set(midX, midY + span * 0.8, midZ + span * 0.8);
        controlsRef.current.target.set(midX, midY, midZ);
      } else {
        camera.position.set(0, 30, 35);
        controlsRef.current.target.set(0, 0, -10);
      }
    } else {
      // Standard 3D Orbit perspective
      camera.position.set(sx, sy + 25, sz + 30);
      controlsRef.current.target.set(sx, sy, sz - 10);
    }

    camera.updateProjectionMatrix();
    controlsRef.current.update();
  }, [viewMode, camera, bounds, sensorPosition]);

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping={true}
      dampingFactor={0.08}
      minDistance={1}
      maxDistance={300}
    />
  );
}
