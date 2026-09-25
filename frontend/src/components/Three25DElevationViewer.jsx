import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Layers } from 'lucide-react';
import { CLASS_COLORS } from '../config/constants';

// Turbo colormap approximation for elevation
function getTurboColor(normalizedHeight) {
  const t = Math.max(0, Math.min(1, normalizedHeight));
  const color = new THREE.Color();
  // Smooth gradient: Blue (0) -> Cyan (0.25) -> Green (0.5) -> Yellow (0.75) -> Red (1.0)
  if (t < 0.25) {
    color.setRGB(0.1 + t * 0.4, 0.4 + t * 2.0, 0.95);
  } else if (t < 0.5) {
    const k = (t - 0.25) / 0.25;
    color.setRGB(0.1 + k * 0.1, 0.9 - k * 0.1, 0.95 - k * 0.6);
  } else if (t < 0.75) {
    const k = (t - 0.5) / 0.25;
    color.setRGB(0.2 + k * 0.75, 0.8 + k * 0.15, 0.35 - k * 0.3);
  } else {
    const k = (t - 0.75) / 0.25;
    color.setRGB(0.95, 0.95 - k * 0.7, 0.05);
  }
  return color;
}

export default function Three25DElevationViewer({
  points = [],
  labels = [],
}) {
  const mountRef = useRef(null);
  const [colorMode, setColorMode] = useState('elevation'); // 'elevation' | 'semantic' | 'resolution'
  const [viewPreset, setViewPreset] = useState('crossSection'); // 'crossSection' | 'isometric' | 'top'
  const [cellCount, setCellCount] = useState(0);

  // Persistent WebGL refs
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const instancedMeshRef = useRef(null);
  const cellsDataRef = useRef([]);

  // Setup WebGL Scene
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 380;
    const height = container.clientHeight || 150;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050913);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 500);
    // Initial Side Cross-Section position
    camera.position.set(0.0, 1.8, -24.0);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0.0, 1.2, 0.0);
    controls.maxPolarAngle = Math.PI / 2 + 0.1;
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00d4ff, 0.8);
    dirLight.position.set(20, 35, -15);
    scene.add(dirLight);

    const dirLightBack = new THREE.DirectionalLight(0xa855f7, 0.5);
    dirLightBack.position.set(-20, -10, 15);
    scene.add(dirLightBack);

    // 6. Ground Grid Base Plane
    const groundGrid = new THREE.GridHelper(30, 30, 0x00d4ff, 0x172742);
    groundGrid.position.y = 0.0;
    scene.add(groundGrid);

    // 7. Reference Baseline Axis Line (Road Corridor Level)
    const baseLineMat = new THREE.LineBasicMaterial({ color: 0x1e3a5f, linewidth: 2 });
    const baseLineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-15, 0.02, 0),
      new THREE.Vector3(15, 0.02, 0),
    ]);
    scene.add(new THREE.Line(baseLineGeo, baseLineMat));

    // 8. Animation Loop
    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // 9. Resize Observer
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Update 2.5D Elevation Column Cells whenever points, labels, or colorMode changes
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene || !points || points.length === 0) return;

    // Remove existing instanced mesh
    if (instancedMeshRef.current) {
      scene.remove(instancedMeshRef.current);
      instancedMeshRef.current.geometry.dispose();
      instancedMeshRef.current.material.dispose();
      instancedMeshRef.current = null;
    }

    // Discretize point cloud into 2.5D cells
    // X corresponds to road lateral Y (-12 to 12m), Z corresponds to height Z (0 to 6m)
    // We project lateral Y onto Three.js X, height Z onto Three.js Y, and longitudinal X onto Three.js Z
    const resolution = 0.55; // Cell resolution in meters
    const gridMap = new Map();

    const step = Math.max(1, Math.floor(points.length / 2800));
    for (let i = 0; i < points.length; i += step) {
      const pt = points[i];
      const lbl = labels[i] !== undefined ? labels[i] : 0;
      // In project: pt[0]=X (forward 0..60m), pt[1]=Y (lateral -8..8m), pt[2]=Z (elevation 0..5m)
      const latY = pt[1];
      const longX = pt[0];
      const elevZ = pt[2];

      // Discretize horizontally into 2.5D spatial cells
      const cellKeyX = Math.floor(latY / resolution);
      const cellKeyZ = Math.floor(longX / (resolution * 1.5));
      const key = `${cellKeyX}_${cellKeyZ}`;

      if (!gridMap.has(key)) {
        gridMap.set(key, {
          x: (cellKeyX + 0.5) * resolution,
          z: (cellKeyZ + 0.5) * (resolution * 1.5),
          minZ: elevZ,
          maxZ: elevZ,
          pointsCount: 1,
          classes: { [lbl]: 1 },
          dominantClass: lbl,
          resolution: resolution,
        });
      } else {
        const cell = gridMap.get(key);
        cell.minZ = Math.min(cell.minZ, elevZ);
        cell.maxZ = Math.max(cell.maxZ, elevZ);
        cell.pointsCount += 1;
        cell.classes[lbl] = (cell.classes[lbl] || 0) + 1;
        if (cell.classes[lbl] > (cell.classes[cell.dominantClass] || 0)) {
          cell.dominantClass = lbl;
        }
      }
    }

    const cells = Array.from(gridMap.values());
    cellsDataRef.current = cells;
    setCellCount(cells.length);

    if (cells.length === 0) return;

    // Unit Box geometry scaled per cell in InstancedMesh
    const unitBoxGeo = new THREE.BoxGeometry(1, 1, 1);
    const boxMat = new THREE.MeshStandardMaterial({
      roughness: 0.35,
      metalness: 0.25,
      transparent: true,
      opacity: 0.92,
    });

    const instMesh = new THREE.InstancedMesh(unitBoxGeo, boxMat, cells.length);
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const scale = new THREE.Vector3();
    const rotation = new THREE.Quaternion();
    const dummyColor = new THREE.Color();

    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      // Three.js coordinates:
      // X = lateral Y (cross-section width)
      // Y = elevation height Z
      // Z = longitudinal forward (depth)
      const height = Math.max(0.12, cell.maxZ);
      const cellW = resolution * 0.92;
      const cellD = resolution * 1.5 * 0.92;

      // Center of box is at height / 2
      position.set(cell.x, height / 2, (cell.z - 25.0) * 0.4);
      scale.set(cellW, height, cellD);
      matrix.compose(position, rotation, scale);
      instMesh.setMatrixAt(i, matrix);

      // Color mapping
      if (colorMode === 'elevation') {
        const normH = Math.max(0, Math.min(1, height / 4.8));
        const c = getTurboColor(normH);
        instMesh.setColorAt(i, c);
      } else if (colorMode === 'semantic') {
        const hex = CLASS_COLORS[cell.dominantClass] || '#64748b';
        dummyColor.set(hex);
        instMesh.setColorAt(i, dummyColor);
      } else {
        // Variable resolution color
        const isFine = cell.dominantClass === 4 || cell.dominantClass === 5;
        dummyColor.set(isFine ? '#00d4ff' : '#a855f7');
        instMesh.setColorAt(i, dummyColor);
      }
    }

    instMesh.instanceMatrix.needsUpdate = true;
    if (instMesh.instanceColor) instMesh.instanceColor.needsUpdate = true;
    instMesh.castShadow = true;
    instMesh.receiveShadow = true;

    scene.add(instMesh);
    instancedMeshRef.current = instMesh;
  }, [points, labels, colorMode]);

  // Handle Preset Camera Changes
  const handleViewPreset = (preset) => {
    setViewPreset(preset);
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    if (preset === 'crossSection') {
      // Direct Cross-Section Side Silhouette
      camera.position.set(0.0, 1.8, -24.0);
      controls.target.set(0.0, 1.2, 0.0);
    } else if (preset === 'isometric') {
      // 3D Angled Elevated Isometric View
      camera.position.set(-16.0, 14.0, -18.0);
      controls.target.set(0.0, 1.5, 0.0);
    } else if (preset === 'top') {
      // Top-Down BEV Elevation Heatmap
      camera.position.set(0.0, 26.0, 0.01);
      controls.target.set(0.0, 0.0, 0.0);
    }
  };

  return (
    <div className="relative w-full h-[150px] bg-[#050913] border border-[#132035] rounded overflow-hidden select-none">
      {/* 3D WebGL Canvas Container */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Overlay Controls: View Presets & Mode Toggles */}
      <div className="absolute top-1.5 left-1.5 flex items-center gap-1 z-10">
        <button
          onClick={() => handleViewPreset('crossSection')}
          className={`px-1.5 py-0.5 rounded text-[9px] font-bold tracking-tight border transition ${
            viewPreset === 'crossSection'
              ? 'bg-[#00d4ff]/25 text-[#00d4ff] border-[#00d4ff]/60 shadow-[0_0_8px_rgba(0,212,255,0.3)]'
              : 'bg-[#09101f]/80 text-[#94a3b8] border-[#172742] hover:text-white'
          }`}
          title="Side Cross-Section View"
        >
          Side Profile
        </button>

        <button
          onClick={() => handleViewPreset('isometric')}
          className={`px-1.5 py-0.5 rounded text-[9px] font-bold tracking-tight border transition ${
            viewPreset === 'isometric'
              ? 'bg-[#00d4ff]/25 text-[#00d4ff] border-[#00d4ff]/60 shadow-[0_0_8px_rgba(0,212,255,0.3)]'
              : 'bg-[#09101f]/80 text-[#94a3b8] border-[#172742] hover:text-white'
          }`}
          title="3D Isometric Elevation Relief"
        >
          3D Relief
        </button>

        <button
          onClick={() => handleViewPreset('top')}
          className={`px-1.5 py-0.5 rounded text-[9px] font-bold tracking-tight border transition ${
            viewPreset === 'top'
              ? 'bg-[#00d4ff]/25 text-[#00d4ff] border-[#00d4ff]/60 shadow-[0_0_8px_rgba(0,212,255,0.3)]'
              : 'bg-[#09101f]/80 text-[#94a3b8] border-[#172742] hover:text-white'
          }`}
          title="Bird's Eye Top View"
        >
          Top Grid
        </button>

        <div className="h-3 w-[1px] bg-[#172742] mx-0.5" />

        {/* Color Mode Switcher */}
        <button
          onClick={() => setColorMode((prev) => (prev === 'elevation' ? 'semantic' : 'elevation'))}
          className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#09101f]/80 text-[#cbd5e1] border border-[#172742] hover:border-[#00d4ff]/50 transition flex items-center gap-1"
          title="Toggle Color Mode (Turbo Height vs Semantic Class)"
        >
          <Layers className="w-2.5 h-2.5 text-[#00d4ff]" />
          <span>{colorMode === 'elevation' ? 'Turbo Height' : 'Semantic'}</span>
        </button>
      </div>

      {/* Turbo Height Colormap Legend Bar on Right */}
      <div className="absolute right-2 top-2 bottom-2 flex flex-col items-center justify-between text-[8px] font-mono text-[#cbd5e1] bg-[#09101f]/85 px-1 py-1 rounded border border-[#172742] pointer-events-none z-10">
        <div className="text-[7.5px] text-[#94a3b8] font-sans font-bold">Height (m)</div>
        <div className="text-red-400 font-bold">5.0</div>
        <div
          className="w-2 flex-1 mx-auto my-0.5 rounded-[1px]"
          style={{
            background: 'linear-gradient(to bottom, #ef4444, #eab308, #10b981, #00d4ff, #2563eb)',
          }}
        />
        <div className="text-yellow-400 font-bold">2.5</div>
        <div className="text-blue-400 font-bold">0.0</div>
      </div>

      {/* Bottom Info Strip: 2.5D Cell Statistics & Three.js Badge */}
      <div className="absolute bottom-1.5 left-2 flex items-center gap-2 text-[8px] font-mono text-[#94a3b8] pointer-events-none z-10">
        <span className="text-[#00d4ff] font-bold bg-[#00d4ff]/10 px-1 py-0.5 rounded border border-[#00d4ff]/20">
          Three.js 2.5D
        </span>
        <span>{cellCount} Pillars</span>
        <span>Res: 0.55m</span>
      </div>
    </div>
  );
}
