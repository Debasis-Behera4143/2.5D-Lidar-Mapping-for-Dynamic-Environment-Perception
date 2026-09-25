/**
 * LiDARScene.jsx
 * Central WebGL 3D Canvas Scene for Real LiDAR Point Clouds and 2.5D Adaptive Grid Maps.
 */

import React from 'react';
import { Canvas } from '@react-three/fiber';
import CameraControls from './CameraControls';
import PointCloud from './PointCloud';
import GridOverlay from './GridOverlay';
import HeightMap from './HeightMap';

export default function LiDARScene({
  bufferData,
  pointSize = 2.5,
  showPoints = true,
  showGrid = true,
  showRangeRings = true,
  showAxes = true,
  viewMode = 'orbit',
  gridCells = [],
  showHeightMap = true,
  heightMapOpacity = 0.45,
  activeClasses = null,
  bounds = null,
  sensorPosition = [0, 0, 0],
  heightExaggeration = 1.0,
}) {
  return (
    <div className="w-full h-full relative bg-[#040711] overflow-hidden select-none">
      <Canvas
        camera={{ position: [0, 25, 30], fov: 50, near: 0.1, far: 600 }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      >
        <color attach="background" args={['#040711']} />

        {/* Ambient & Directional Scene Lighting */}
        <ambientLight intensity={0.9} />
        <directionalLight position={[25, 50, 25]} intensity={1.0} />

        {/* Camera Controls */}
        <CameraControls
          viewMode={viewMode}
          bounds={bounds}
          sensorPosition={sensorPosition}
        />

        {/* Technical Ground Grid & Sensor Overlays */}
        <GridOverlay
          showGrid={showGrid}
          showRangeRings={showRangeRings}
          showAxes={showAxes}
          sensorPosition={sensorPosition}
        />

        {/* Real LiDAR Point Cloud */}
        <PointCloud
          bufferData={bufferData}
          pointSize={pointSize}
          visible={showPoints}
          heightExaggeration={heightExaggeration}
        />

        {/* Real 2.5D Adaptive Variable-Resolution Grid */}
        <HeightMap
          cells={gridCells}
          activeClasses={activeClasses}
          opacity={heightMapOpacity}
          visible={showHeightMap}
        />
      </Canvas>
    </div>
  );
}
