/**
 * GridOverlay.jsx
 * Technical ground grid, metric range rings (10m, 20m, 30m, 40m, 50m), and sensor coordinate axes.
 * NO decorative/fake vehicle models.
 */

import React from 'react';
import * as THREE from 'three';

export default function GridOverlay({
  showRangeRings = true,
  showAxes = true,
  showGrid = true,
  sensorPosition = [0, 0, 0],
}) {
  const rings = [10, 20, 30, 40, 50];

  return (
    <group>
      {/* Cartesian Reference Grid */}
      {showGrid && (
        <gridHelper
          args={[100, 50, '#1e3a5f', '#0b1424']}
          position={[0, -1.73, 0]}
        />
      )}

      {/* Metric Sensor Range Rings */}
      {showRangeRings &&
        rings.map((r) => (
          <mesh
            key={r}
            rotation={[-Math.PI / 2, 0, 0]}
            position={[0, -1.72, 0]}
          >
            <ringGeometry args={[r - 0.06, r + 0.06, 64]} />
            <meshBasicMaterial
              color="#0284c7"
              transparent={true}
              opacity={0.25}
              side={THREE.DoubleSide}
            />
          </mesh>
        ))}

      {/* LiDAR Sensor Origin Axes (RGB = XYZ) */}
      {showAxes && (
        <primitive
          object={new THREE.AxesHelper(2.5)}
          position={sensorPosition}
        />
      )}
    </group>
  );
}
