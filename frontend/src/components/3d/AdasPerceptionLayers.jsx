/**
 * AdasPerceptionLayers.jsx
 * High-fidelity 3D Autonomous Vehicle Perception Digital Twin Layers.
 *
 * Implements:
 * 1. TrackedVehicles: Sleek 3D car models for other vehicles with glowing bounding cages,
 *    ground radar reticles, and overhead HUD badges ("Target #1: Car · 10.4m ahead").
 * 2. RoadsideTrees: Authentic 3D natural trees (cylinder trunk + tiered emerald foliage canopies)
 *    lining the roadside verges.
 * 3. BuildingStructures: 3D modern architectural volumes with glowing window bands and roof parapets.
 * 4. AdasRadarWavesAndLanes: Concentric glowing radar distance rings (10m - 50m), forward perception
 *    radar cone, and highway lane guidance corridor matching reference ADAS visualizations.
 * 5. TrackedPedestrians & Poles: 3D pedestrian avatars with amber tracking cages.
 */

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Html } from '@react-three/drei';

/**
 * 1. 3D Car Model for Other Tracked Vehicles
 */
function SingleTrackedCar({
  id = 1,
  position = [1.65, 0.65, -10.2],
  size = { length: 4.5, width: 1.8, height: 1.4 },
  distance = 10.4,
  label = 'Vehicle',
  color = '#0284c7', // Cyber blue metallic
  showBadges = true,
}) {
  const cageRef = useRef();
  const reticleRef = useRef();

  // Subtle pulsing animation on the ground reticle
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (reticleRef.current) {
      reticleRef.current.rotation.z = t * 0.8;
      const s = 1 + Math.sin(t * 3) * 0.04;
      reticleRef.current.scale.set(s, s, 1);
    }
  });

  const carLength = size.length || 4.2;
  const carWidth = size.width || 1.8;
  const carHeight = size.height || 1.4;

  return (
    <group position={position}>
      {/* --- 3D Car Geometry --- */}
      {/* Lower Main Chassis */}
      <mesh position={[0, -0.15, 0]}>
        <boxGeometry args={[carWidth * 0.96, carHeight * 0.48, carLength * 0.96]} />
        <meshStandardMaterial
          color={color}
          metalness={0.88}
          roughness={0.22}
          envMapIntensity={1.0}
        />
      </mesh>

      {/* Aerodynamic Cabin / Windshield Glass */}
      <mesh position={[0, carHeight * 0.24, -carLength * 0.06]}>
        <boxGeometry args={[carWidth * 0.86, carHeight * 0.44, carLength * 0.54]} />
        <meshStandardMaterial
          color="#060e1e"
          metalness={0.9}
          roughness={0.08}
          transparent
          opacity={0.92}
        />
      </mesh>

      {/* Front Hood Scoop / Inset */}
      <mesh position={[0, 0.05, -carLength * 0.36]}>
        <boxGeometry args={[carWidth * 0.72, 0.08, carLength * 0.22]} />
        <meshStandardMaterial color="#0f172a" metalness={0.7} roughness={0.4} />
      </mesh>

      {/* Glowing Headlights (Front is -Z) */}
      <mesh position={[carWidth * 0.36, -0.08, -carLength * 0.49]}>
        <boxGeometry args={[carWidth * 0.2, 0.1, 0.04]} />
        <meshBasicMaterial color="#38bdf8" />
      </mesh>
      <mesh position={[-carWidth * 0.36, -0.08, -carLength * 0.49]}>
        <boxGeometry args={[carWidth * 0.2, 0.1, 0.04]} />
        <meshBasicMaterial color="#38bdf8" />
      </mesh>

      {/* Glowing Taillights (Rear is +Z) */}
      <mesh position={[carWidth * 0.36, 0.02, carLength * 0.49]}>
        <boxGeometry args={[carWidth * 0.22, 0.1, 0.04]} />
        <meshBasicMaterial color="#ef4444" />
      </mesh>
      <mesh position={[-carWidth * 0.36, 0.02, carLength * 0.49]}>
        <boxGeometry args={[carWidth * 0.22, 0.1, 0.04]} />
        <meshBasicMaterial color="#ef4444" />
      </mesh>

      {/* 4 Wheels (Rubber tires + alloy rims) */}
      {[
        [-carWidth * 0.5, -carHeight * 0.28, -carLength * 0.3], // Front Left
        [carWidth * 0.5, -carHeight * 0.28, -carLength * 0.3],  // Front Right
        [-carWidth * 0.5, -carHeight * 0.28, carLength * 0.3],  // Rear Left
        [carWidth * 0.5, -carHeight * 0.28, carLength * 0.3],   // Rear Right
      ].map((wPos, idx) => (
        <group key={idx} position={wPos} rotation={[0, 0, Math.PI / 2]}>
          <mesh>
            <cylinderGeometry args={[0.34, 0.34, 0.18, 18]} />
            <meshStandardMaterial color="#0f172a" roughness={0.8} />
          </mesh>
          <mesh position={[0, 0.01, 0]}>
            <cylinderGeometry args={[0.2, 0.2, 0.19, 12]} />
            <meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.1} />
          </mesh>
        </group>
      ))}

      {/* --- 3D Bounding Cage (Neon Cyan ADAS Wireframe) --- */}
      <group ref={cageRef}>
        {/* Wireframe outer box */}
        <mesh>
          <boxGeometry args={[carWidth + 0.2, carHeight + 0.25, carLength + 0.25]} />
          <meshBasicMaterial color="#00e5ff" wireframe transparent opacity={0.65} />
        </mesh>
        {/* Semi-transparent volume tint */}
        <mesh>
          <boxGeometry args={[carWidth + 0.2, carHeight + 0.25, carLength + 0.25]} />
          <meshBasicMaterial color="#00e5ff" transparent opacity={0.06} />
        </mesh>
      </group>

      {/* --- Ground Radar Reticle (Pulsing Target Ring on Road) --- */}
      <group position={[0, -carHeight * 0.44, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <group ref={reticleRef}>
          {/* Outer circular target ring */}
          <lineSegments>
            <ringGeometry args={[carLength * 0.65, carLength * 0.68, 32]} />
            <meshBasicMaterial color="#00e5ff" transparent opacity={0.7} />
          </lineSegments>
          {/* Inner ring */}
          <lineSegments>
            <ringGeometry args={[carLength * 0.42, carLength * 0.44, 24]} />
            <meshBasicMaterial color="#38bdf8" transparent opacity={0.4} />
          </lineSegments>
        </group>
        {/* Ground shadow plane */}
        <mesh position={[0, 0, -0.01]}>
          <planeGeometry args={[carWidth * 1.6, carLength * 1.2]} />
          <meshBasicMaterial color="#000000" transparent opacity={0.5} />
        </mesh>
      </group>

      {/* --- Overhead HUD Target Badge & Leader Line --- */}
      {showBadges && (
        <>
          {/* Vertical Leader Line from Car Roof to Badge */}
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[new Float32Array([0, carHeight * 0.5, 0, 0, carHeight * 0.5 + 1.2, 0]), 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#00e5ff" transparent opacity={0.8} />
          </lineSegments>

          {/* Floating ADAS Target Card */}
          <Html position={[0, carHeight * 0.5 + 1.35, 0]} center distanceFactor={20}>
            <div className="bg-[#040e1e]/95 border border-[#00e5ff] rounded px-2.5 py-1 text-center shadow-xl shadow-cyan-950/60 backdrop-blur-md pointer-events-none select-none">
              <div className="flex items-center gap-1.5 justify-center">
                <span className="w-2 h-2 rounded-full bg-[#00e5ff] animate-ping" />
                <span className="text-[10px] font-mono font-bold text-white tracking-wider">
                  TARGET #{id}: {label.toUpperCase()}
                </span>
              </div>
              <div className="text-[9.5px] font-mono text-[#38bdf8] flex items-center justify-between gap-3 mt-0.5 border-t border-[#133054] pt-0.5">
                <span>DIST: <b className="text-white">{distance.toFixed(1)}m</b></span>
                <span className="text-emerald-400 font-bold">TRACKED</span>
              </div>
            </div>
          </Html>
        </>
      )}
    </group>
  );
}

/**
 * TrackedVehicles Group
 * Renders detected cars or high-fidelity defaults matching Reference Image 2.
 */
export function TrackedVehicles({
  detectedObjects = [],
  show = true,
  showBadges = true,
  frameIndex = 0,
}) {
  if (!show) return null;

  // Filter detected vehicle objects
  const vehicleObjs = (detectedObjects || []).filter(
    (o) => o.class_id === 4 || o.class_name === 'vehicle'
  );

  // If no vehicles detected yet, provide realistic reference vehicles ahead
  const vehiclesToRender = vehicleObjs.length > 0 ? vehicleObjs : [
    {
      id: 1,
      class_name: 'vehicle',
      center: { x: 10.4, y: -1.65, z: -0.9 },
      size: { length: 4.5, width: 1.8, height: 1.4 },
      distance_m: 10.4,
    },
    {
      id: 2,
      class_name: 'vehicle',
      center: { x: 22.0, y: 1.95, z: -0.9 },
      size: { length: 4.2, width: 1.75, height: 1.4 },
      distance_m: 22.1,
    },
  ];

  return (
    <group>
      {vehiclesToRender.map((obj, i) => {
        const posX = -(obj.center?.y || 0);
        const posY = 0.65;
        const posZ = -(obj.center?.x || (18 + i * 16));
        const dist = obj.distance_m || Math.sqrt(posX * posX + posZ * posZ);

        return (
          <SingleTrackedCar
            key={obj.id || i}
            id={obj.id || i + 1}
            position={[posX, posY, posZ]}
            size={obj.size || { length: 4.5, width: 1.8, height: 1.4 }}
            distance={dist}
            label={obj.class_name || 'Vehicle'}
            color={i % 2 === 0 ? '#0284c7' : '#2563eb'}
            showBadges={showBadges}
          />
        );
      })}
    </group>
  );
}

/**
 * 2. Natural 3D Roadside Trees
 * Realistic trunk + layered emerald foliage canopies along the roadside tree lines.
 */
function SingleTree({ position = [0, 0, 0], scale = 1, seed = 0 }) {
  const trunkHeight = 1.9 * scale;
  const trunkRadius = 0.22 * scale;

  // Varied emerald green shades
  const canopyColors = [
    '#10b981', // Emerald 500
    '#059669', // Emerald 600
    '#047857', // Emerald 700
    '#34d399', // Emerald 400
  ];
  const col1 = canopyColors[seed % 4];
  const col2 = canopyColors[(seed + 1) % 4];
  const col3 = canopyColors[(seed + 2) % 4];

  return (
    <group position={position}>
      {/* Wood Cylinder Trunk */}
      <mesh position={[0, trunkHeight / 2, 0]}>
        <cylinderGeometry args={[trunkRadius * 0.75, trunkRadius, trunkHeight, 8]} />
        <meshStandardMaterial color="#422817" roughness={0.9} />
      </mesh>

      {/* Shrub / Grass ring at trunk base */}
      <mesh position={[0, 0.08, 0]}>
        <cylinderGeometry args={[trunkRadius * 2.2, trunkRadius * 2.6, 0.16, 8]} />
        <meshStandardMaterial color="#065f46" roughness={0.9} />
      </mesh>

      {/* Lower Foliage Canopy Tier */}
      <mesh position={[0, trunkHeight + 0.7 * scale, 0]}>
        <icosahedronGeometry args={[1.35 * scale, 1]} />
        <meshStandardMaterial color={col1} roughness={0.65} metalness={0.05} />
      </mesh>

      {/* Middle Foliage Canopy Tier */}
      <mesh position={[0.1 * scale, trunkHeight + 1.6 * scale, -0.05 * scale]}>
        <icosahedronGeometry args={[1.05 * scale, 1]} />
        <meshStandardMaterial color={col2} roughness={0.65} metalness={0.05} />
      </mesh>

      {/* Upper Crown Foliage Tier */}
      <mesh position={[-0.05 * scale, trunkHeight + 2.3 * scale, 0.05 * scale]}>
        <icosahedronGeometry args={[0.75 * scale, 1]} />
        <meshStandardMaterial color={col3} roughness={0.6} metalness={0.05} />
      </mesh>
    </group>
  );
}

export function RoadsideTrees({
  detectedObjects = [],
  show = true,
}) {
  if (!show) return null;

  // Pre-generate roadside tree coordinates along left and right highway verges
  const treePositions = useMemo(() => {
    const list = [];
    // Left tree verge (y = +7.2m in KITTI -> Three.js X = -7.2m)
    // Right tree verge (y = -7.2m in KITTI -> Three.js X = +7.2m)
    const zSteps = [-35, -28, -21, -14, -7, 0, 7, 14, 21, 28, 35, 42, 49];

    zSteps.forEach((zVal, i) => {
      // Left verge tree with slight organic wobble
      const wobbleX_L = -7.2 + Math.sin(i * 1.7) * 0.4;
      const scale_L = 0.9 + Math.cos(i * 2.3) * 0.18;
      list.push({ pos: [wobbleX_L, 0, -zVal], scale: scale_L, seed: i });

      // Right verge tree with slight organic wobble
      const wobbleX_R = 7.2 + Math.cos(i * 1.5) * 0.4;
      const scale_R = 0.95 + Math.sin(i * 2.1) * 0.18;
      list.push({ pos: [wobbleX_R, 0, -zVal], scale: scale_R, seed: i + 10 });
    });

    return list;
  }, []);

  return (
    <group>
      {treePositions.map((t, idx) => (
        <SingleTree
          key={idx}
          position={t.pos}
          scale={t.scale}
          seed={t.seed}
        />
      ))}
    </group>
  );
}

/**
 * 3. 3D Architectural Modern Buildings
 * Extruded urban structures along the outer perimeter with glowing window strips.
 */
function SingleBuilding({ position = [0, 0, 0], size = [10, 12, 16], seed = 0 }) {
  const [width, height, depth] = size;

  return (
    <group position={position}>
      {/* Main Structural Core */}
      <mesh position={[0, height / 2, 0]}>
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial
          color="#0b1322"
          metalness={0.7}
          roughness={0.35}
        />
      </mesh>

      {/* Structural Wireframe Edges */}
      <mesh position={[0, height / 2, 0]}>
        <boxGeometry args={[width * 1.002, height * 1.002, depth * 1.002]} />
        <meshBasicMaterial color="#1e3a6a" wireframe transparent opacity={0.4} />
      </mesh>

      {/* Horizontal Glowing Window Bands (Cyan & Warm Amber digital twin lighting) */}
      {[0.25, 0.45, 0.65, 0.82].map((ratio, idx) => {
        const winY = height * ratio;
        const winColor = (seed + idx) % 2 === 0 ? '#38bdf8' : '#f59e0b';
        return (
          <mesh key={idx} position={[0, winY, 0]}>
            <boxGeometry args={[width + 0.04, 0.4, depth + 0.04]} />
            <meshBasicMaterial color={winColor} transparent opacity={0.7} />
          </mesh>
        );
      })}

      {/* Rooftop Parapet Border */}
      <mesh position={[0, height + 0.25, 0]}>
        <boxGeometry args={[width * 0.94, 0.5, depth * 0.94]} />
        <meshStandardMaterial color="#142036" metalness={0.5} roughness={0.5} />
      </mesh>

      {/* Rooftop HVAC equipment box */}
      <mesh position={[width * 0.2, height + 0.7, depth * 0.2]}>
        <boxGeometry args={[width * 0.35, 0.9, depth * 0.3]} />
        <meshStandardMaterial color="#1e293b" metalness={0.8} roughness={0.3} />
      </mesh>
    </group>
  );
}

export function BuildingStructures({
  detectedObjects = [],
  show = true,
}) {
  if (!show) return null;

  // Pre-configured architectural buildings flanking left and right avenues
  const buildings = useMemo(() => [
    // Left side buildings (beyond tree line at X = -14m to -18m)
    { pos: [-16, 0, 18], size: [9, 12, 18], seed: 1 },
    { pos: [-16.5, 0, -5], size: [10, 16, 22], seed: 2 },
    { pos: [-16, 0, -32], size: [9, 14, 20], seed: 3 },
    { pos: [-17, 0, -56], size: [11, 18, 24], seed: 4 },

    // Right side buildings (beyond tree line at X = +14m to +18m)
    { pos: [16, 0, 18], size: [9, 14, 18], seed: 5 },
    { pos: [16.5, 0, -6], size: [10, 12, 20], seed: 6 },
    { pos: [16, 0, -32], size: [9, 17, 22], seed: 7 },
    { pos: [17, 0, -56], size: [11, 15, 24], seed: 8 },
  ], []);

  return (
    <group>
      {buildings.map((b, idx) => (
        <SingleBuilding
          key={idx}
          position={b.pos}
          size={b.size}
          seed={b.seed}
        />
      ))}
    </group>
  );
}

/**
 * 4. ADAS Radar Waves and Highway Drivable Lanes
 * Concentric glowing circular range rings, forward perception radar cone,
 * and highway lane corridor matching Reference Image 2 & 3.
 */
export function AdasRadarWavesAndLanes({
  egoPos = [0, 0.65, 0],
  showRadar = true,
  showLanes = true,
}) {
  const radarSweepRef = useRef();

  useFrame((state) => {
    if (radarSweepRef.current) {
      const t = state.clock.getElapsedTime();
      // Rotate subtle scan wave
      radarSweepRef.current.rotation.z = -t * 0.9;
    }
  });

  const [egoX, , egoZ] = egoPos;
  const radarRings = [10, 20, 30, 40, 50];

  return (
    <group>
      {/* --- Concentric ADAS Radar Distance Rings --- */}
      {showRadar && (
        <group position={[egoX, 0.02, egoZ]} rotation={[-Math.PI / 2, 0, 0]}>
          {radarRings.map((radius) => (
            <group key={radius}>
              {/* Circular Line Ring */}
              <lineSegments>
                <ringGeometry args={[radius - 0.04, radius + 0.04, 64]} />
                <meshBasicMaterial
                  color="#00e5ff"
                  transparent
                  opacity={radius <= 20 ? 0.45 : 0.28}
                />
              </lineSegments>

              {/* Range Distance Label */}
              <Html position={[radius, 0, 0]} center distanceFactor={28}>
                <div className="text-[8.5px] font-mono font-bold text-[#00e5ff]/80 select-none pointer-events-none px-1 bg-[#040814]/70 rounded">
                  {radius}M
                </div>
              </Html>
            </group>
          ))}

          {/* Forward Radar Perception Fan/Cone (±25 deg spanning 50m forward) */}
          {/* Note: in rotated frame, -Y is forward (-Z in Three.js) */}
          <mesh rotation={[0, 0, -Math.PI / 2]}>
            <ringGeometry args={[0.5, 48, 32, 1, -Math.PI * 0.16, Math.PI * 0.32]} />
            <meshBasicMaterial
              color="#00e5ff"
              transparent
              opacity={0.06}
              side={THREE.DoubleSide}
            />
          </mesh>

          {/* Rotating Subtle Radar Sweep Beam */}
          <group ref={radarSweepRef}>
            <mesh>
              <ringGeometry args={[1, 48, 16, 1, 0, Math.PI * 0.2]} />
              <meshBasicMaterial
                color="#38bdf8"
                transparent
                opacity={0.05}
                side={THREE.DoubleSide}
              />
            </mesh>
          </group>
        </group>
      )}

      {/* --- Highway Drivable Lane Ribbon & Roadway --- */}
      {showLanes && (
        <group position={[0, 0.01, egoZ]}>
          {/* Smooth Dark Roadbed Plane (Length 90m, Width 8.8m) centered on roadway */}
          <mesh position={[0, -0.015, -15]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[8.8, 100]} />
            <meshStandardMaterial
              color="#060c18"
              roughness={0.9}
              metalness={0.1}
            />
          </mesh>

          {/* Road Surface Center Dividing Line (Dashed White/Amber at X = 0) */}
          {[-6, -14, -22, -30, -38, -46, -54, -62].map((zVal, idx) => (
            <mesh key={`center-dash-${idx}`} position={[0, 0.008, zVal]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.16, 3.5]} />
              <meshBasicMaterial color="#fcd34d" transparent opacity={0.65} />
            </mesh>
          ))}

          {/* Left Passing Lane Center (X = -2.2m) Dashed Guide */}
          {[-6, -14, -22, -30, -38, -46, -54, -62].map((zVal, idx) => (
            <mesh key={`left-dash-${idx}`} position={[-2.2, 0.006, zVal]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.12, 2.5]} />
              <meshBasicMaterial color="#38bdf8" transparent opacity={0.4} />
            </mesh>
          ))}

          {/* Right Cruising Lane Center (X = +2.2m) Dashed Guide */}
          {[-6, -14, -22, -30, -38, -46, -54, -62].map((zVal, idx) => (
            <mesh key={`right-dash-${idx}`} position={[2.2, 0.006, zVal]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[0.12, 2.5]} />
              <meshBasicMaterial color="#38bdf8" transparent opacity={0.4} />
            </mesh>
          ))}

          {/* Left Highway Curb / Verge Barrier (X = -4.2m) */}
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[new Float32Array([-4.2, 0.02, 25, -4.2, 0.02, -75]), 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#38bdf8" transparent opacity={0.7} />
          </lineSegments>

          {/* Right Highway Curb / Verge Barrier (X = +4.2m) */}
          <lineSegments>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[new Float32Array([4.2, 0.02, 25, 4.2, 0.02, -75]), 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#38bdf8" transparent opacity={0.7} />
          </lineSegments>
        </group>
      )}

      {/* --- Active Ego Dynamic Avoidance Trajectory Ribbon --- */}
      {showLanes && (
        <group>
          {/* Planned Autonomous Avoidance Path Markers (Glowing S-curve on road) */}
          {Array.from({ length: 45 }, (_, idx) => {
            const z = -(idx * 1.0);
            const dist = -z;
            let px = 0;
            if (dist >= 4.0 && dist < 12.0) {
              const t = (dist - 4.0) / 8.0;
              px = -2.4 * (0.5 - 0.5 * Math.cos(t * Math.PI));
            } else if (dist >= 12.0 && dist < 24.0) {
              px = -2.4;
            } else if (dist >= 24.0 && dist < 32.0) {
              const t = (dist - 24.0) / 8.0;
              px = -2.4 * (0.5 + 0.5 * Math.cos(t * Math.PI));
            } else {
              px = 0;
            }
            return (
              <mesh key={`path-${idx}`} position={[px, 0.02, z]} rotation={[-Math.PI / 2, 0, 0]}>
                <planeGeometry args={[0.22, 0.65]} />
                <meshBasicMaterial
                  color={dist >= 8.0 && dist <= 24.0 ? '#10b981' : '#00e5ff'}
                  transparent
                  opacity={0.75}
                />
              </mesh>
            );
          })}
        </group>
      )}
    </group>
  );
}

/**
 * 5. Tracked Pedestrian & Street Elements
 */
export function TrackedPedestrians({
  detectedObjects = [],
  show = true,
  showBadges = true,
  frameIndex = 0,
}) {
  if (!show) return null;

  const pedObjs = (detectedObjects || []).filter(
    (o) => o.class_id === 5 || o.class_name === 'pedestrian'
  );

  const pedestriansToRender = pedObjs.length > 0 ? pedObjs : [
    {
      id: 3,
      class_name: 'pedestrian',
      center: { x: 6.5, y: 4.85, z: -0.6 },
      size: { length: 0.9, width: 0.7, height: 1.8 },
      distance_m: 8.1,
    }
  ];

  return (
    <group>
      {pedestriansToRender.map((obj, idx) => {
        const posX = -(obj.center?.y || 4.8);
        const posY = 0.9;
        const posZ = -(obj.center?.x || 6.5) - frameIndex * 0.12;
        const dist = obj.distance_m || Math.sqrt(posX * posX + posZ * posZ);

        return (
          <group key={obj.id || idx} position={[posX, posY, posZ]}>
            {/* Low-poly Stylized Pedestrian Avatar */}
            {/* Head */}
            <mesh position={[0, 0.6, 0]}>
              <sphereGeometry args={[0.16, 12, 12]} />
              <meshStandardMaterial color="#fcd34d" metalness={0.2} roughness={0.5} />
            </mesh>
            {/* Torso */}
            <mesh position={[0, 0.22, 0]}>
              <boxGeometry args={[0.38, 0.55, 0.24]} />
              <meshStandardMaterial color="#eab308" metalness={0.4} roughness={0.4} />
            </mesh>
            {/* Legs */}
            <mesh position={[-0.1, -0.32, 0]}>
              <boxGeometry args={[0.14, 0.55, 0.16]} />
              <meshStandardMaterial color="#475569" roughness={0.7} />
            </mesh>
            <mesh position={[0.1, -0.32, 0]}>
              <boxGeometry args={[0.14, 0.55, 0.16]} />
              <meshStandardMaterial color="#475569" roughness={0.7} />
            </mesh>

            {/* Amber ADAS Bounding Cage */}
            <mesh>
              <boxGeometry args={[0.8, 1.8, 0.8]} />
              <meshBasicMaterial color="#f59e0b" wireframe transparent opacity={0.7} />
            </mesh>

            {/* Ground Yellow Reticle */}
            <mesh position={[0, -0.88, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0.5, 0.55, 18]} />
              <meshBasicMaterial color="#f59e0b" transparent opacity={0.6} />
            </mesh>

            {/* Floating HUD Badge */}
            {showBadges && (
              <Html position={[0, 1.15, 0]} center distanceFactor={18}>
                <div className="bg-[#1f1604]/95 border border-[#f59e0b] rounded px-2 py-0.5 text-center shadow-lg shadow-amber-950/50 backdrop-blur-md pointer-events-none select-none">
                  <div className="text-[9.5px] font-mono font-bold text-amber-300">
                    PEDESTRIAN · {dist.toFixed(1)}m
                  </div>
                </div>
              </Html>
            )}
          </group>
        );
      })}
    </group>
  );
}
