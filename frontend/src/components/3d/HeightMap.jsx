/**
 * HeightMap.jsx
 * 2.5D Adaptive Variable-Resolution Grid Overlay.
 * Directly renders cells from Member 3 AdaptiveGridMapper:
 * - Coarse cells (e.g. 1.0m) for low-importance / static regions
 * - Fine subdivided cells (e.g. 0.25m) for dynamic / high-importance regions
 * - Renders as clean geometric grid tiles without blocking vertical columns.
 */

import React, { useMemo } from 'react';
import * as THREE from 'three';
import { CLASS_COLOR_MAP } from '../../app/config';

export default function HeightMap({
  cells = [],
  activeClasses = null,
  opacity = 0.4,
  visible = true,
  showWireframe = true,
}) {
  const filteredCells = useMemo(() => {
    if (!cells || cells.length === 0) return [];
    return cells.filter((c) => {
      if (activeClasses && activeClasses[c.dominant_class] === false) {
        return false;
      }
      return true;
    });
  }, [cells, activeClasses]);

  if (!visible || filteredCells.length === 0) return null;

  return (
    <group>
      {filteredCells.map((cell, idx) => {
        const res = cell.resolution || 0.5;
        const isFine = cell.level === 'fine' || res <= 0.3;
        const dominantCls = cell.dominant_class ?? 0;
        const colorHex = CLASS_COLOR_MAP[dominantCls] || '#38bdf8';

        // Map from KITTI to Three.js coordinates:
        // Three X = -cell.center_y, Three Y = cell.mean_height or ground baseline, Three Z = -cell.center_x
        const posX = -(cell.center_y || 0);
        const elevationY = typeof cell.mean_height === 'number' ? cell.mean_height : -1.7;
        const posZ = -(cell.center_x || 0);

        const tileWidth = res * 0.96;
        const tileDepth = res * 0.96;
        const tileHeight = 0.04; // Sleek 2.5D elevation surface tile

        const borderColor = isFine ? '#00f0ff' : '#475569';

        return (
          <group key={idx} position={[posX, elevationY, posZ]}>
            {/* Flat elevation occupancy tile */}
            <mesh>
              <boxGeometry args={[tileWidth, tileHeight, tileDepth]} />
              <meshStandardMaterial
                color={colorHex}
                transparent={true}
                opacity={opacity}
                roughness={0.6}
              />
            </mesh>

            {/* Crisp outline showing grid subdivision */}
            {showWireframe && (
              <lineSegments>
                <edgesGeometry args={[new THREE.BoxGeometry(tileWidth, tileHeight, tileDepth)]} />
                <lineBasicMaterial
                  color={borderColor}
                  transparent={true}
                  opacity={isFine ? 0.9 : 0.4}
                />
              </lineSegments>
            )}
          </group>
        );
      })}
    </group>
  );
}
