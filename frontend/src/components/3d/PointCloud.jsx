/**
 * PointCloud.jsx
 * High-performance WebGL Point Cloud rendering via Three.js BufferGeometry with GPU buffer reuse.
 * Renders actual LiDAR XYZ coordinates and 8-class semantic colors without artificial primitives.
 */

import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

export default function PointCloud({
  bufferData,
  pointSize = 2.5,
  visible = true,
  heightExaggeration = 1.0,
}) {
  const pointsRef = useRef();
  const geometryRef = useRef(new THREE.BufferGeometry());

  useEffect(() => {
    if (!geometryRef.current) return;
    const geo = geometryRef.current;

    if (bufferData && bufferData.count > 0) {
      let positions = bufferData.positions;

      // Apply height exaggeration only if != 1.0 without corrupting source data
      if (heightExaggeration !== 1.0) {
        positions = new Float32Array(bufferData.positions);
        for (let i = 1; i < positions.length; i += 3) {
          positions[i] = positions[i] * heightExaggeration;
        }
      }

      // Reuse or reallocate BufferAttribute
      if (
        !geo.attributes.position ||
        geo.attributes.position.array.length !== positions.length
      ) {
        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geo.setAttribute('color', new THREE.BufferAttribute(bufferData.colors, 3));
      } else {
        geo.attributes.position.array.set(positions);
        geo.attributes.position.needsUpdate = true;
        geo.attributes.color.array.set(bufferData.colors);
        geo.attributes.color.needsUpdate = true;
      }
      geo.computeBoundingSphere();
    } else {
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(0), 3));
      geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(0), 3));
    }
  }, [bufferData, heightExaggeration]);

  if (!visible || !bufferData || bufferData.count === 0) return null;

  return (
    <points ref={pointsRef} geometry={geometryRef.current}>
      <pointsMaterial
        size={pointSize}
        vertexColors={true}
        sizeAttenuation={true}
        transparent={false}
        opacity={1.0}
      />
    </points>
  );
}
