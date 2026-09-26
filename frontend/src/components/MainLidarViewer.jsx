/**
 * MainLidarViewer.jsx
 * Master 3D / 2.5D Semantic LiDAR Point Cloud & Adaptive Grid Environment.
 *
 * Features:
 * 1. Real dense LiDAR Point Cloud rendered via THREE.BufferGeometry + Float32Array on GPU
 * 2. 8 Semantic classes with precise color mapping
 * 3. Class visibility toggles that modify the WebGL point buffer directly
 * 4. Point size control slider (small / medium / large)
 * 5. Ego vehicle model moving forward during sequence playback
 * 6. Camera Presets: 3D Orbit, Bird Eye (Top-Down), Ego Sensor POV, Side Profile, Front View, Reset View, Fit Scene
 * 7. Point click / hover inspection HUD (X, Y, Z, Class, Confidence, Height, Frame)
 * 8. Real 2.5D Adaptive Grid cell ground tiles
 * 9. Reference-style callout leader badges & XYZ orientation gizmo
 */

import React, { useRef, useState, useMemo, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { CLASS_COLORS, CLASS_NAMES } from '../config/constants';
import {
  Maximize2,
  RefreshCw,
  MapPin,
  Eye,
  Car,
  TreePine,
  Building2,
  Radar,
  Navigation,
} from 'lucide-react';
import {
  TrackedVehicles,
  RoadsideTrees,
  BuildingStructures,
  AdasRadarWavesAndLanes,
  TrackedPedestrians,
} from './3d/AdasPerceptionLayers';

// Pre-compute float RGB colors for all classes to eliminate runtime allocations
const PRECOMPUTED_COLORS = Object.entries(CLASS_COLORS).reduce((acc, [k, hex]) => {
  const c = new THREE.Color(hex);
  acc[k] = [c.r, c.g, c.b];
  return acc;
}, {});
const DEFAULT_RGB = [0.58, 0.64, 0.72];

/**
 * Real LiDAR Point Cloud Component (THREE.Points + Float32Array on GPU)
 * Optimized with direct TypedArray buffer generation and throttled raycasting.
 */
function RealLidarPoints({
  points = [],
  labels = [],
  confidences = [],
  activeClasses = {},
  pointSize = 0.08,
  frameId = '000000',
  onHoverPoint,
  onClickPoint,
}) {
  const pointsRef = useRef();
  const geometryRef = useRef();
  const lastHoverTime = useRef(0);

  // Convert raw points into WebGL buffer attributes using pre-allocated TypedArrays
  const { positions, colors, count, originalIndices } = useMemo(() => {
    if (!points || points.length === 0) {
      return {
        positions: new Float32Array(0),
        colors: new Float32Array(0),
        count: 0,
        originalIndices: new Int32Array(0),
      };
    }

    const n = points.length;
    const pos = new Float32Array(n * 3);
    const col = new Float32Array(n * 3);
    const origIdx = new Int32Array(n);
    let validCount = 0;

    for (let i = 0; i < n; i++) {
      const pt = points[i];
      const lbl = labels[i] !== undefined ? labels[i] : 7;

      // Check class visibility filter
      if (activeClasses[lbl] === false) {
        continue;
      }

      // Coordinate transformation:
      // KITTI / Project LiDAR: X forward, Y lateral, Z height
      // Three.js: X right (-Y), Y up (+Z), Z depth (-X)
      const idx3 = validCount * 3;
      pos[idx3] = -(pt[1] !== undefined ? pt[1] : 0);
      pos[idx3 + 1] = pt[2] !== undefined ? pt[2] : 0;
      pos[idx3 + 2] = -(pt[0] !== undefined ? pt[0] : 0);

      // Fast RGB color lookup without new THREE.Color() allocations
      const rgb = PRECOMPUTED_COLORS[lbl] || DEFAULT_RGB;
      col[idx3] = rgb[0];
      col[idx3 + 1] = rgb[1];
      col[idx3 + 2] = rgb[2];

      origIdx[validCount] = i;
      validCount++;
    }

    return {
      positions: validCount === n ? pos : pos.subarray(0, validCount * 3),
      colors: validCount === n ? col : col.subarray(0, validCount * 3),
      count: validCount,
      originalIndices: origIdx,
    };
  }, [points, labels, activeClasses]);

  // Update geometry buffers when points or visibility changes
  useEffect(() => {
    if (!geometryRef.current) return;
    const geo = geometryRef.current;

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.attributes.position.needsUpdate = true;
    geo.attributes.color.needsUpdate = true;
    geo.computeBoundingSphere();
  }, [positions, colors]);

  // Throttled raycasting for point hover inspection to prevent CPU stutter
  const handlePointerMove = (e) => {
    e.stopPropagation();
    const now = performance.now();
    if (now - lastHoverTime.current < 65) return; // Cap hover detection at ~15 FPS
    lastHoverTime.current = now;

    if (e.index !== undefined && originalIndices[e.index] !== undefined) {
      const origIdx = originalIndices[e.index];
      const pt = points[origIdx];
      const lbl = labels[origIdx] !== undefined ? labels[origIdx] : 7;
      const conf = confidences[origIdx] !== undefined ? confidences[origIdx] : 0.95;

      onHoverPoint &&
        onHoverPoint({
          x: pt[0],
          y: pt[1],
          z: pt[2],
          classId: lbl,
          className: CLASS_NAMES[lbl] || 'Other',
          confidence: conf,
          height: pt[2],
          frameId: frameId,
        });
    }
  };

  const handlePointerOut = () => {
    onHoverPoint && onHoverPoint(null);
  };

  const handlePointerDown = (e) => {
    e.stopPropagation();
    if (e.index !== undefined && originalIndices[e.index] !== undefined) {
      const origIdx = originalIndices[e.index];
      const pt = points[origIdx];
      const lbl = labels[origIdx] !== undefined ? labels[origIdx] : 7;
      const conf = confidences[origIdx] !== undefined ? confidences[origIdx] : 0.95;

      onClickPoint &&
        onClickPoint({
          x: pt[0],
          y: pt[1],
          z: pt[2],
          classId: lbl,
          className: CLASS_NAMES[lbl] || 'Other',
          confidence: conf,
          height: pt[2],
          frameId: frameId,
        });
    }
  };

  if (count === 0) return null;

  return (
    <points
      ref={pointsRef}
      onPointerMove={handlePointerMove}
      onPointerOut={handlePointerOut}
      onPointerDown={handlePointerDown}
    >
      <bufferGeometry ref={geometryRef}>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={pointSize}
        vertexColors
        sizeAttenuation
        transparent
        opacity={0.94}
      />
    </points>
  );
}

/**
 * High-performance 2.5D Adaptive Grid Mesh on Ground Plane
 * Uses 1 InstancedMesh for ground tile fills and 1 single LineSegments for all wireframe borders
 * (Reduces GPU draw calls from 2000+ down to 2, eliminating render lag completely).
 */
function AdaptiveGrid3D({ cells = [], showGrid = true, baseResolution = 1.0 }) {
  const instancedMeshRef = useRef();
  const lineGeometryRef = useRef();

  const hasCells = Boolean(showGrid && cells && cells.length > 0);

  // Pre-compute wireframe line segments for all grid cells in a single continuous buffer
  const { linePositions, lineColors, cellCount } = useMemo(() => {
    if (!hasCells) {
      return { linePositions: new Float32Array(0), lineColors: new Float32Array(0), cellCount: 0 };
    }

    const count = cells.length;
    // Each cell has 4 border line segments = 8 vertices = 24 floats
    const pos = new Float32Array(count * 24);
    const col = new Float32Array(count * 24);

    const cyanR = 0.0, cyanG = 0.82, cyanB = 1.0;
    const indigoR = 0.39, indigoG = 0.40, indigoB = 0.95;

    for (let i = 0; i < count; i++) {
      const cell = cells[i];
      const posX = -(cell.center_y || 0);
      const posZ = -(cell.center_x || 0);
      const res = (cell.resolution || baseResolution) * 0.94;
      const isFine = res <= 0.3 || (cell.importance_score && cell.importance_score > 0.6);

      const r = isFine ? cyanR : indigoR;
      const g = isFine ? cyanG : indigoG;
      const b = isFine ? cyanB : indigoB;

      const h = res / 2;
      const y = -0.02;

      // 4 border segments: (-h,-h) -> (h,-h) -> (h,h) -> (-h,h) -> (-h,-h)
      const baseIdx = i * 24;
      const pts = [
        posX - h, y, posZ - h, posX + h, y, posZ - h,
        posX + h, y, posZ - h, posX + h, y, posZ + h,
        posX + h, y, posZ + h, posX - h, y, posZ + h,
        posX - h, y, posZ + h, posX - h, y, posZ - h,
      ];

      for (let j = 0; j < 24; j += 3) {
        pos[baseIdx + j] = pts[j];
        pos[baseIdx + j + 1] = pts[j + 1];
        pos[baseIdx + j + 2] = pts[j + 2];
        col[baseIdx + j] = r;
        col[baseIdx + j + 1] = g;
        col[baseIdx + j + 2] = b;
      }
    }

    return { linePositions: pos, lineColors: col, cellCount: count };
  }, [cells, hasCells, baseResolution]);

  // Update InstancedMesh matrices and colors for ground fills
  useEffect(() => {
    if (!instancedMeshRef.current || !hasCells || cellCount === 0) return;
    const mesh = instancedMeshRef.current;
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const rotation = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0));
    const scale = new THREE.Vector3();
    const dummyColor = new THREE.Color();

    for (let i = 0; i < cellCount; i++) {
      const cell = cells[i];
      const posX = -(cell.center_y || 0);
      const posZ = -(cell.center_x || 0);
      const res = (cell.resolution || baseResolution) * 0.94;
      const isFine = res <= 0.3 || (cell.importance_score && cell.importance_score > 0.6);

      position.set(posX, -0.02, posZ);
      scale.set(res, res, 1);
      matrix.compose(position, rotation, scale);
      mesh.setMatrixAt(i, matrix);

      dummyColor.set(isFine ? '#00d2ff' : '#6366f1');
      mesh.setColorAt(i, dummyColor);
    }

    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  }, [cells, hasCells, cellCount, baseResolution]);

  // Update wireframe line buffer attributes
  useEffect(() => {
    if (!lineGeometryRef.current || !hasCells) return;
    const geo = lineGeometryRef.current;
    geo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));
    geo.attributes.position.needsUpdate = true;
    geo.attributes.color.needsUpdate = true;
  }, [linePositions, lineColors, hasCells]);

  if (!showGrid || !cells || cells.length === 0) {
    return (
      <gridHelper
        args={[100, 50, 0x00d4ff, 0x142844]}
        position={[0, -0.05, -20]}
      />
    );
  }

  return (
    <group>
      {/* All cell floor plane quads rendered in 1 single draw call */}
      <instancedMesh
        ref={instancedMeshRef}
        args={[null, null, cellCount]}
      >
        <planeGeometry args={[1, 1]} />
        <meshBasicMaterial transparent opacity={0.25} />
      </instancedMesh>

      {/* All cell wireframe borders rendered in 1 single draw call */}
      <lineSegments>
        <bufferGeometry ref={lineGeometryRef} />
        <lineBasicMaterial vertexColors transparent opacity={0.65} />
      </lineSegments>
    </group>
  );
}

/**
 * Ego Vehicle Model (moves forward during playback)
 */
function EgoVehicle({ position = [0, 0.65, -4], show = true }) {
  if (!show) return null;

  return (
    <group position={position}>
      {/* Chassis Body */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1.9, 1.1, 3.8]} />
        <meshStandardMaterial color="#f8fafc" metalness={0.85} roughness={0.2} />
      </mesh>
      {/* Cabin Roof / Dark Tinted Glass */}
      <mesh position={[0, 0.45, -0.2]}>
        <boxGeometry args={[1.6, 0.75, 2.1]} />
        <meshStandardMaterial color="#091322" metalness={0.3} roughness={0.1} />
      </mesh>
      {/* Roof LiDAR Puck (Cyan Glow) */}
      <mesh position={[0, 0.95, 0.1]}>
        <cylinderGeometry args={[0.2, 0.2, 0.22, 16]} />
        <meshStandardMaterial color="#00ffcc" metalness={0.9} roughness={0.1} />
      </mesh>
      {/* Red Taillights */}
      <mesh position={[0.7, 0.1, 1.91]}>
        <boxGeometry args={[0.28, 0.14, 0.04]} />
        <meshBasicMaterial color="#ef4444" />
      </mesh>
      <mesh position={[-0.7, 0.1, 1.91]}>
        <boxGeometry args={[0.28, 0.14, 0.04]} />
        <meshBasicMaterial color="#ef4444" />
      </mesh>
      {/* Headlights (Cyan/White) */}
      <mesh position={[0.7, 0.1, -1.91]}>
        <boxGeometry args={[0.28, 0.14, 0.04]} />
        <meshBasicMaterial color="#38bdf8" />
      </mesh>
      <mesh position={[-0.7, 0.1, -1.91]}>
        <boxGeometry args={[0.28, 0.14, 0.04]} />
        <meshBasicMaterial color="#38bdf8" />
      </mesh>
    </group>
  );
}

/**
 * Camera Controller for Presets and Ego Follow
 */
function CameraRig({
  cameraMode = 'orbit',
  egoPos = [0, 0.65, -4],
  controlsRef,
}) {
  const { camera } = useThree();

  useEffect(() => {
    if (!controlsRef.current) return;
    const controls = controlsRef.current;

    if (cameraMode === 'birdEye') {
      // Top-Down Bird's Eye View
      camera.position.set(0, 52, egoPos[2] - 12);
      controls.target.set(0, 0, egoPos[2] - 12);
      controls.update();
    } else if (cameraMode === 'egoPOV') {
      // Ego Sensor POV looking straight forward
      camera.position.set(egoPos[0], egoPos[1] + 1.2, egoPos[2] + 0.5);
      controls.target.set(egoPos[0], egoPos[1] + 1.0, egoPos[2] - 25);
      controls.update();
    } else if (cameraMode === 'sideProfile') {
      // Side Profile
      camera.position.set(28, 6, egoPos[2] - 10);
      controls.target.set(0, 1.5, egoPos[2] - 10);
      controls.update();
    } else if (cameraMode === 'frontView') {
      // Direct Front View looking back at approaching car
      camera.position.set(0, 3, egoPos[2] - 30);
      controls.target.set(0, 1.2, egoPos[2]);
      controls.update();
    } else if (cameraMode === 'orbit') {
      // Default 3D Orbit View
      camera.position.set(0, 15, egoPos[2] + 18);
      controls.target.set(0, 1.2, egoPos[2] - 14);
      controls.update();
    }
  }, [cameraMode, camera, controlsRef]);

  // Smoothly follow the moving vehicle during playback when in Ego POV or Orbit
  useFrame(() => {
    if (cameraMode === 'egoPOV' && controlsRef.current) {
      const controls = controlsRef.current;
      camera.position.set(egoPos[0], egoPos[1] + 1.2, egoPos[2] + 0.5);
      controls.target.set(egoPos[0], egoPos[1] + 1.0, egoPos[2] - 25);
      controls.update();
    }
  });

  return null;
}

export default function MainLidarViewer({
  points = [],
  labels = [],
  confidences = [],
  adaptiveMap = null,
  activeClasses = {},
  frameId = '000000',
  frameIndex = 0,
  baseResolution = 1.0,
  detectedObjects = [],
  resetToken = 0,
  onHoverPoint,
  hoveredPoint: propHoveredPoint,
  onClickPoint,
  selectedPoint: propSelectedPoint,
}) {
  const controlsRef = useRef();
  const [cameraMode, setCameraMode] = useState('orbit'); // 'orbit' | 'birdEye' | 'egoPOV' | 'sideProfile' | 'frontView'
  const [pointSize, setPointSize] = useState(0.07);
  const [showGrid, setShowGrid] = useState(true);
  const [showEgo, setShowEgo] = useState(true);
  const [showPoints, setShowPoints] = useState(true);
  const [showCars, setShowCars] = useState(true);
  const [showTrees, setShowTrees] = useState(true);
  const [showBuildings, setShowBuildings] = useState(true);
  const [showRadar, setShowRadar] = useState(true);
  const [showLanes, setShowLanes] = useState(true);
  const [showCallouts, setShowCallouts] = useState(true);

  // Local state for hover/selected point so mouse movements don't cause root App re-renders
  const [internalHoveredPoint, setInternalHoveredPoint] = useState(null);
  const [internalSelectedPoint, setInternalSelectedPoint] = useState(null);

  const hoveredPoint = propHoveredPoint !== undefined && propHoveredPoint !== null ? propHoveredPoint : internalHoveredPoint;
  const selectedPoint = propSelectedPoint !== undefined && propSelectedPoint !== null ? propSelectedPoint : internalSelectedPoint;

  const handleHoverPoint = (pt) => {
    setInternalHoveredPoint(pt);
    if (onHoverPoint) onHoverPoint(pt);
  };

  const handleClickPoint = (pt) => {
    setInternalSelectedPoint(pt);
    if (onClickPoint) onClickPoint(pt);
  };

  // Move the user's ego vehicle forward with the active playback frame.
  const egoPos = useMemo(() => [0, 0.65, -(frameIndex * 4.0)], [frameIndex]);

  const handleResetView = () => {
    setCameraMode('orbit');
    if (controlsRef.current) {
      controlsRef.current.reset();
      controlsRef.current.target.set(0, 1.2, -18);
    }
  };

  const handleFitScene = () => {
    if (controlsRef.current) {
      controlsRef.current.target.set(0, 1.5, -20);
    }
  };

  useEffect(() => {
    if (resetToken > 0) handleResetView();
  }, [resetToken]);

  return (
    <div className="relative flex-1 bg-[#040814] border border-[#14233c] rounded-lg overflow-hidden select-none flex flex-col h-[280px] md:h-auto min-h-[250px] md:min-h-0">
      {/* Top Header & Floating Toolbar */}
      <div className="absolute top-2 left-2 right-2 md:top-2 md:left-3 md:right-3 z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-2 md:gap-0 pointer-events-none">
        <div className="text-[10px] md:text-xs font-bold text-white tracking-tight flex items-center gap-2 bg-[#050b18]/85 px-2 py-1 rounded border border-[#162744] backdrop-blur-sm pointer-events-auto">
          <span className="hidden sm:inline">2.5D Semantic Elevation Map & 3D ADAS Digital Twin</span>
          <span className="sm:hidden">3D Digital Twin</span>
        </div>

        {/* Top-Right Floating Camera & Settings Toolbar */}
        <div className="flex flex-wrap items-center gap-1 md:gap-1.5 bg-[#050b18]/85 p-1 rounded-md border border-[#162744] backdrop-blur-sm pointer-events-auto text-[10px] font-mono w-full md:w-auto">
          {/* Camera Preset Buttons */}
          <div className="flex items-center gap-1 bg-[#0a1528] p-0.5 rounded border border-[#1a3258] overflow-x-auto max-w-full scrollbar-none">
            <button
              onClick={() => setCameraMode('orbit')}
              className={`px-1.5 py-0.5 rounded ${
                cameraMode === 'orbit' ? 'bg-blue-600 text-white font-bold' : 'text-[#8da8cf] hover:text-white'
              }`}
              title="3D Orbit View"
            >
              3D Orbit
            </button>
            <button
              onClick={() => setCameraMode('birdEye')}
              className={`px-1.5 py-0.5 rounded ${
                cameraMode === 'birdEye' ? 'bg-blue-600 text-white font-bold' : 'text-[#8da8cf] hover:text-white'
              }`}
              title="Bird's Eye Top-Down View"
            >
              Bird Eye
            </button>
            <button
              onClick={() => setCameraMode('egoPOV')}
              className={`px-1.5 py-0.5 rounded ${
                cameraMode === 'egoPOV' ? 'bg-blue-600 text-white font-bold' : 'text-[#8da8cf] hover:text-white'
              }`}
              title="Ego Vehicle Sensor POV"
            >
              Ego POV
            </button>
            <button
              onClick={() => setCameraMode('sideProfile')}
              className={`px-1.5 py-0.5 rounded ${
                cameraMode === 'sideProfile' ? 'bg-blue-600 text-white font-bold' : 'text-[#8da8cf] hover:text-white'
              }`}
              title="Side Profile View"
            >
              Side
            </button>
            <button
              onClick={() => setCameraMode('frontView')}
              className={`px-1.5 py-0.5 rounded ${
                cameraMode === 'frontView' ? 'bg-blue-600 text-white font-bold' : 'text-[#8da8cf] hover:text-white'
              }`}
              title="Front Perspective View"
            >
              Front
            </button>
          </div>

          {/* Reset & Fit */}
          <button
            onClick={handleResetView}
            className="p-1 rounded bg-[#0a1528] border border-[#1a3258] text-[#8da8cf] hover:text-white hover:border-[#38bdf8]"
            title="Reset Default View"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
          <button
            onClick={handleFitScene}
            className="p-1 rounded bg-[#0a1528] border border-[#1a3258] text-[#8da8cf] hover:text-white hover:border-[#38bdf8]"
            title="Fit Scene to Viewport"
          >
            <Maximize2 className="w-3 h-3" />
          </button>

          <div className="h-3 w-[1px] bg-[#1a3258] mx-0.5" />

          {/* Point Size Control */}
          <div className="flex items-center gap-1 text-[#8da8cf] px-1">
            <span className="text-[9px]">Pt:</span>
            <input
              type="range"
              min="0.03"
              max="0.18"
              step="0.01"
              value={pointSize}
              onChange={(e) => setPointSize(parseFloat(e.target.value))}
              className="w-12 h-1 bg-[#162744] rounded appearance-none cursor-pointer accent-cyan-400"
              title={`Point Size: ${pointSize.toFixed(2)}`}
            />
          </div>

          {/* 3D Perception Digital Twin Layer Toggles */}
          <button
            onClick={() => setShowCars(!showCars)}
            className={`px-1.5 py-0.5 rounded border text-[9px] flex items-center gap-1 ${
              showCars
                ? 'bg-blue-950/70 border-blue-500/60 text-blue-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle 3D Tracked Cars"
          >
            Cars
          </button>
          <button
            onClick={() => setShowTrees(!showTrees)}
            className={`px-1.5 py-0.5 rounded border text-[9px] flex items-center gap-1 ${
              showTrees
                ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle 3D Roadside Trees"
          >
            Trees
          </button>
          <button
            onClick={() => setShowBuildings(!showBuildings)}
            className={`px-1.5 py-0.5 rounded border text-[9px] flex items-center gap-1 ${
              showBuildings
                ? 'bg-indigo-950/70 border-indigo-500/60 text-indigo-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle 3D Architectural Buildings"
          >
            Bldgs
          </button>
          <button
            onClick={() => setShowRadar(!showRadar)}
            className={`px-1.5 py-0.5 rounded border text-[9px] ${
              showRadar
                ? 'bg-cyan-950/70 border-cyan-500/60 text-cyan-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle ADAS Radar Range Rings"
          >
            Radar
          </button>
          <button
            onClick={() => setShowLanes(!showLanes)}
            className={`px-1.5 py-0.5 rounded border text-[9px] ${
              showLanes
                ? 'bg-cyan-950/70 border-cyan-500/60 text-cyan-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle Highway Lane Corridor"
          >
            Lanes
          </button>
          <button
            onClick={() => setShowPoints(!showPoints)}
            className={`px-1.5 py-0.5 rounded border text-[9px] ${
              showPoints
                ? 'bg-purple-950/70 border-purple-500/60 text-purple-300 font-bold'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle Raw Point Cloud"
          >
            Points
          </button>
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`px-1.5 py-0.5 rounded border text-[9px] ${
              showGrid
                ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-400'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle 2.5D Adaptive Grid"
          >
            Grid
          </button>
          <button
            onClick={() => setShowCallouts(!showCallouts)}
            className={`px-1.5 py-0.5 rounded border text-[9px] ${
              showCallouts
                ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-400'
                : 'bg-[#0a1528] border-[#1a3258] text-[#597499]'
            }`}
            title="Toggle Leader Callouts & HUD Badges"
          >
            Badges
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div className="w-full h-full">
        <Canvas
          camera={{ position: [0, 15, 18], fov: 48, near: 0.1, far: 450 }}
          gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
        >
          <color attach="background" args={['#040814']} />
          <fog attach="fog" args={['#040814', 45, 190]} />

          <ambientLight intensity={0.95} />
          <directionalLight position={[20, 45, 20]} intensity={1.2} />

          <OrbitControls
            ref={controlsRef}
            enableDamping
            dampingFactor={0.08}
            minDistance={3}
            maxDistance={140}
            maxPolarAngle={Math.PI / 2 - 0.01}
            target={[0, 1.2, -18]}
          />

          <CameraRig
            cameraMode={cameraMode}
            egoPos={egoPos}
            controlsRef={controlsRef}
          />

          {/* ADAS Autonomous Highway Lanes & Concentric Radar Waves */}
          <AdasRadarWavesAndLanes
            egoPos={egoPos}
            showRadar={showRadar}
            showLanes={showLanes}
          />

          {/* 3D Natural Roadside Trees along Highway Curbs */}
          <RoadsideTrees
            detectedObjects={detectedObjects}
            show={showTrees}
          />

          {/* 3D Modern Architectural Buildings flanking the road */}
          <BuildingStructures
            detectedObjects={detectedObjects}
            show={showBuildings}
          />

          {/* 3D Tracked Other Vehicles (Cars with Bounding Cages, Radar Reticles & HUD Badges) */}
          <TrackedVehicles
            detectedObjects={detectedObjects}
            show={showCars}
            showBadges={showCallouts}
            frameIndex={frameIndex}
          />

          {/* 3D Tracked Pedestrians */}
          <TrackedPedestrians
            detectedObjects={detectedObjects}
            show={showCars}
            showBadges={showCallouts}
            frameIndex={frameIndex}
          />

          {/* Real LiDAR Points Buffer (Toggleable on/off) */}
          {showPoints && (
            <RealLidarPoints
              points={points}
              labels={labels}
              confidences={confidences}
              activeClasses={activeClasses}
              pointSize={pointSize}
              frameId={frameId}
              onHoverPoint={handleHoverPoint}
              onClickPoint={handleClickPoint}
            />
          )}

          {/* 2.5D Adaptive Grid Ground Tiles */}
          <AdaptiveGrid3D
            cells={adaptiveMap?.cells}
            showGrid={showGrid}
            baseResolution={baseResolution}
          />

          {/* Ego Vehicle (at origin of sensor coordinate system) */}
          <EgoVehicle position={egoPos} show={showEgo} />
        </Canvas>
      </div>

      {/* CALLOUT BADGES WITH LEADER LINES */}
      {showCallouts && (
        <>
          <div className="hidden md:block absolute top-11 left-6 pointer-events-none flex flex-col items-center">
            <div className="bg-[#140608]/90 border border-[#ef4444] rounded px-2.5 py-1 text-center shadow-lg shadow-red-950/40 backdrop-blur-sm">
              <div className="text-[11px] font-bold text-white">Wall (Non-drivable)</div>
              <div className="text-[10px] text-[#fca5a5]">Height: ~2.5 m</div>
            </div>
            <div className="w-[1px] h-7 bg-gradient-to-b from-[#ef4444] to-transparent transform -rotate-12 origin-top" />
          </div>

          <div className="hidden md:block absolute top-11 left-[36%] pointer-events-none flex flex-col items-center">
            <div className="bg-[#180824]/90 border border-[#d946ef] rounded px-2.5 py-1 text-center shadow-lg shadow-fuchsia-950/40 backdrop-blur-sm">
              <div className="text-[11px] font-bold text-white">Vehicle (Dynamic)</div>
              <div className="text-[10px] text-[#f0abfc]">Height: ~1.5 m</div>
            </div>
            <div className="w-[1px] h-10 bg-gradient-to-b from-[#d946ef] to-transparent" />
          </div>

          <div className="hidden md:block absolute top-11 right-16 pointer-events-none flex flex-col items-center">
            <div className="bg-[#051c12]/90 border border-[#10b981] rounded px-2.5 py-1 text-center shadow-lg shadow-emerald-950/40 backdrop-blur-sm">
              <div className="text-[11px] font-bold text-white">Tree (Static)</div>
              <div className="text-[10px] text-[#6ee7b7]">Height: ~5 m</div>
            </div>
            <div className="w-[1px] h-9 bg-gradient-to-b from-[#10b981] to-transparent transform rotate-12 origin-top" />
          </div>

          <div className="hidden md:block absolute top-[48%] right-8 pointer-events-none flex flex-col items-center">
            <div className="bg-[#1f1905]/90 border border-[#eab308] rounded px-2.5 py-1 text-center shadow-lg shadow-amber-950/40 backdrop-blur-sm">
              <div className="text-[11px] font-bold text-white">Pedestrian (Dynamic)</div>
              <div className="text-[10px] text-[#fde047]">Height: ~1.7 m</div>
            </div>
            <div className="w-[1px] h-8 bg-gradient-to-b from-[#eab308] to-transparent transform -rotate-25 origin-top" />
          </div>

          <div className="hidden md:block absolute bottom-6 right-20 pointer-events-none flex flex-col items-center">
            <div className="bg-[#071933]/90 border border-[#1d64f2] rounded px-2.5 py-1 text-center shadow-lg shadow-blue-950/40 backdrop-blur-sm">
              <div className="text-[11px] font-bold text-white">Drivable Road</div>
              <div className="text-[10px] text-[#93c5fd]">Height: ~0.0 - 0.5 m</div>
            </div>
            <div className="w-[1px] h-6 bg-gradient-to-b from-[#1d64f2] to-transparent transform -rotate-45 origin-top" />
          </div>
        </>
      )}

      {/* 3D Coordinate Gizmo at Bottom-Left */}
      <div className="absolute bottom-4 left-4 pointer-events-none flex items-center gap-2 bg-[#061022]/85 border border-[#172e50] px-2.5 py-1.5 rounded backdrop-blur-sm">
        <div className="relative w-8 h-8 flex items-center justify-center">
          <div className="absolute bottom-2 left-3 w-0.5 h-5 bg-[#10b981]" />
          <span className="absolute -top-1 left-2 text-[8px] font-bold text-[#10b981]">Z</span>

          <div className="absolute bottom-2 left-3 w-5 h-0.5 bg-[#ef4444]" />
          <span className="absolute bottom-0 right-0 text-[8px] font-bold text-[#ef4444]">X</span>

          <div className="absolute bottom-2 left-3 w-3.5 h-0.5 bg-[#38bdf8] transform -rotate-45 origin-bottom-left" />
          <span className="absolute top-1 right-2 text-[8px] font-bold text-[#38bdf8]">Y</span>
        </div>
        <span className="text-[10px] font-bold text-[#7ca2d4]">Z (Height)</span>
      </div>

      {/* POINT INSPECTION TOOLTIP HUD (HOVER / CLICK) */}
      {(hoveredPoint || selectedPoint) && (
        <div
          className="absolute top-12 left-4 z-20 bg-[#081224]/95 border border-[#1d4ed8] p-2.5 rounded-lg shadow-xl shadow-blue-950/60 backdrop-blur-md text-[10px] font-mono pointer-events-none w-44"
        >
          <div className="text-[10.5px] font-bold text-cyan-400 border-b border-[#162744] pb-1 mb-1.5 flex items-center gap-1">
            <MapPin className="w-3 h-3 text-cyan-400" />
            <span>POINT INFORMATION</span>
          </div>
          {(() => {
            const p = hoveredPoint || selectedPoint;
            return (
              <div className="space-y-1 text-[#b5cbdf]">
                <div className="flex justify-between">
                  <span className="text-[#6484a6]">X / Y:</span>
                  <span className="text-white font-bold">{p.x?.toFixed(2)}m, {p.y?.toFixed(2)}m</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#6484a6]">Height (Z):</span>
                  <span className="text-emerald-400 font-bold">{p.height?.toFixed(2)} m</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#6484a6]">Class:</span>
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-bold" style={{ backgroundColor: CLASS_COLORS[p.classId] || '#64748b', color: '#ffffff' }}>
                    {p.className}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#6484a6]">Confidence:</span>
                  <span className="text-yellow-400 font-bold">{(p.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#6484a6]">Frame:</span>
                  <span className="text-white">{p.frameId}</span>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
