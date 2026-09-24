import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Eye, Grid, MapPin } from 'lucide-react';
import { CLASS_COLORS } from '../config/constants';

export default function MainLidarViewer({
  points = [],
  labels = [],
  annotations = [],
  colorMode = 'semantic', // 'semantic' | 'elevation'
  onToggleColorMode,
}) {
  const mountRef = useRef(null);
  const controlsRef = useRef(null);
  const cameraRef = useRef(null);

  const [activeView, setActiveView] = useState('Driver');
  const [showGrid, setShowGrid] = useState(true);
  const [showAnnotations, setShowAnnotations] = useState(true);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight || 450;

    // 1. Scene & Background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050913);

    // 2. Camera Setup (Driver Perspective matching reference)
    const camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 200);
    camera.position.set(-0.2, 5.8, -12.0); // Driver eye behind ego vehicle
    cameraRef.current = camera;

    // 3. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0.0, 1.2, 14.0);
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00d4ff, 0.5);
    dirLight.position.set(10, 20, -10);
    scene.add(dirLight);

    // 6. Point Cloud Buffer Geometry
    if (points && points.length > 0) {
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(points.length * 3);
      const colors = new Float32Array(points.length * 3);

      const colorObj = new THREE.Color();

      for (let i = 0; i < points.length; i++) {
        const pt = points[i];
        // Coordinates mapping: Lateral Y -> Three X, Height Z -> Three Y, Forward X -> Three Z
        positions[i * 3] = pt[1];
        positions[i * 3 + 1] = pt[2];
        positions[i * 3 + 2] = pt[0];

        if (colorMode === 'elevation') {
          // Turbo colormap approximation for height (0 to 5m)
          const normZ = Math.max(0, Math.min(1, pt[2] / 4.8));
          colorObj.setHSL(0.65 - normZ * 0.65, 0.95, 0.52);
        } else {
          // Semantic class color
          const lbl = labels[i] !== undefined ? labels[i] : 0;
          const hex = CLASS_COLORS[lbl] || '#64748b';
          colorObj.set(hex);
        }

        colors[i * 3] = colorObj.r;
        colors[i * 3 + 1] = colorObj.g;
        colors[i * 3 + 2] = colorObj.b;
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const pointMaterial = new THREE.PointsMaterial({
        size: 2.4,
        vertexColors: true,
        transparent: true,
        opacity: 0.92,
      });

      const pointCloud = new THREE.Points(geometry, pointMaterial);
      scene.add(pointCloud);
    }

    // 7. Multi-Resolution Adaptive Grid Bands on Drivable Surface (Matching Screenshot)
    if (showGrid) {
      const gridGroup = new THREE.Group();

      // Band 1: 0 - 10 m (Fine 5cm - Cyan/Blue)
      const b1PlaneGeo = new THREE.PlaneGeometry(8.4, 18.0);
      const b1PlaneMat = new THREE.MeshBasicMaterial({
        color: 0x0055ff,
        transparent: true,
        opacity: 0.28,
        side: THREE.DoubleSide,
      });
      const b1Plane = new THREE.Mesh(b1PlaneGeo, b1PlaneMat);
      b1Plane.rotation.x = -Math.PI / 2;
      b1Plane.position.set(0, 0.02, 1.0);
      gridGroup.add(b1Plane);

      // Fine wireframe lines for Band 1 (step = 0.8m)
      const b1Lines = [];
      for (let x = -4.2; x <= 4.2; x += 0.8) {
        b1Lines.push(x, 0.03, -8.0, x, 0.03, 10.0);
      }
      for (let z = -8.0; z <= 10.0; z += 0.8) {
        b1Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      }
      const b1LinesGeo = new THREE.BufferGeometry();
      b1LinesGeo.setAttribute('position', new THREE.Float32BufferAttribute(b1Lines, 3));
      gridGroup.add(new THREE.LineSegments(b1LinesGeo, new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.65 })));

      // Band 2: 10 - 25 m (Mid 10cm - Purple/Violet)
      const b2PlaneGeo = new THREE.PlaneGeometry(8.4, 15.0);
      const b2PlaneMat = new THREE.MeshBasicMaterial({
        color: 0x7c3aed,
        transparent: true,
        opacity: 0.25,
        side: THREE.DoubleSide,
      });
      const b2Plane = new THREE.Mesh(b2PlaneGeo, b2PlaneMat);
      b2Plane.rotation.x = -Math.PI / 2;
      b2Plane.position.set(0, 0.02, 17.5);
      gridGroup.add(b2Plane);

      const b2Lines = [];
      for (let x = -4.2; x <= 4.2; x += 1.6) {
        b2Lines.push(x, 0.03, 10.0, x, 0.03, 25.0);
      }
      for (let z = 10.0; z <= 25.0; z += 1.6) {
        b2Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      }
      const b2LinesGeo = new THREE.BufferGeometry();
      b2LinesGeo.setAttribute('position', new THREE.Float32BufferAttribute(b2Lines, 3));
      gridGroup.add(new THREE.LineSegments(b2LinesGeo, new THREE.LineBasicMaterial({ color: 0xa855f7, transparent: true, opacity: 0.55 })));

      // Band 3: 25 - 50 m (Coarse 25cm - Yellow)
      const b3PlaneGeo = new THREE.PlaneGeometry(8.4, 25.0);
      const b3PlaneMat = new THREE.MeshBasicMaterial({
        color: 0xd97706,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
      });
      const b3Plane = new THREE.Mesh(b3PlaneGeo, b3PlaneMat);
      b3Plane.rotation.x = -Math.PI / 2;
      b3Plane.position.set(0, 0.02, 37.5);
      gridGroup.add(b3Plane);

      const b3Lines = [];
      for (let x = -4.2; x <= 4.2; x += 2.8) {
        b3Lines.push(x, 0.03, 25.0, x, 0.03, 50.0);
      }
      for (let z = 25.0; z <= 50.0; z += 2.8) {
        b3Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      }
      const b3LinesGeo = new THREE.BufferGeometry();
      b3LinesGeo.setAttribute('position', new THREE.Float32BufferAttribute(b3Lines, 3));
      gridGroup.add(new THREE.LineSegments(b3LinesGeo, new THREE.LineBasicMaterial({ color: 0xfacc15, transparent: true, opacity: 0.45 })));

      // Band 4: 50 - 100 m (Very Coarse 50cm - Orange/Red)
      const b4PlaneGeo = new THREE.PlaneGeometry(8.4, 50.0);
      const b4PlaneMat = new THREE.MeshBasicMaterial({
        color: 0xdc2626,
        transparent: true,
        opacity: 0.18,
        side: THREE.DoubleSide,
      });
      const b4Plane = new THREE.Mesh(b4PlaneGeo, b4PlaneMat);
      b4Plane.rotation.x = -Math.PI / 2;
      b4Plane.position.set(0, 0.02, 75.0);
      gridGroup.add(b4Plane);

      const b4Lines = [];
      for (let x = -4.2; x <= 4.2; x += 4.2) {
        b4Lines.push(x, 0.03, 50.0, x, 0.03, 100.0);
      }
      for (let z = 50.0; z <= 100.0; z += 5.0) {
        b4Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      }
      const b4LinesGeo = new THREE.BufferGeometry();
      b4LinesGeo.setAttribute('position', new THREE.Float32BufferAttribute(b4Lines, 3));
      gridGroup.add(new THREE.LineSegments(b4LinesGeo, new THREE.LineBasicMaterial({ color: 0xf87171, transparent: true, opacity: 0.4 })));

      scene.add(gridGroup);
    }

    // 8. Dynamic Vehicles Representation
    // Ego-Vehicle (White car at origin)
    const egoGeo = new THREE.BoxGeometry(1.8, 1.4, 4.2);
    const egoMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc,
      roughness: 0.2,
      metalness: 0.8,
    });
    const egoMesh = new THREE.Mesh(egoGeo, egoMat);
    egoMesh.position.set(0, 0.75, 0);
    scene.add(egoMesh);

    // Ego windshield
    const egoGlassGeo = new THREE.BoxGeometry(1.6, 0.7, 1.8);
    const egoGlassMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.75 });
    const egoGlass = new THREE.Mesh(egoGlassGeo, egoGlassMat);
    egoGlass.position.set(0, 1.25, -0.2);
    scene.add(egoGlass);

    // Front dynamic vehicle (Pink/Magenta car matching reference screenshot)
    const frontCarGeo = new THREE.BoxGeometry(1.8, 1.3, 4.2);
    const frontCarMat = new THREE.MeshStandardMaterial({
      color: 0xd946ef,
      roughness: 0.3,
      metalness: 0.7,
    });
    const frontCar = new THREE.Mesh(frontCarGeo, frontCarMat);
    frontCar.position.set(0.4, 0.75, 15.5);
    scene.add(frontCar);

    // Far vehicle ahead (at 32m)
    const farCar = new THREE.Mesh(frontCarGeo, frontCarMat);
    farCar.position.set(-1.6, 0.75, 32.0);
    scene.add(farCar);

    // 9. Coordinate Axes Gizmo (Z Height Green, Y Lateral Red, X Forward Blue)
    const axesGroup = new THREE.Group();
    // X Forward (Blue)
    const dirX = new THREE.Vector3(0, 0, 1);
    axesGroup.add(new THREE.ArrowHelper(dirX, new THREE.Vector3(0, 0, 0), 2.2, 0x00d4ff, 0.4, 0.2));
    // Y Lateral (Red)
    const dirY = new THREE.Vector3(1, 0, 0);
    axesGroup.add(new THREE.ArrowHelper(dirY, new THREE.Vector3(0, 0, 0), 2.2, 0xef4444, 0.4, 0.2));
    // Z Height (Green)
    const dirZ = new THREE.Vector3(0, 1, 0);
    axesGroup.add(new THREE.ArrowHelper(dirZ, new THREE.Vector3(0, 0, 0), 2.2, 0x10b981, 0.4, 0.2));
    axesGroup.position.set(-6.5, 0.2, -6.0);
    scene.add(axesGroup);

    // 10. Animation Render Loop
    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 450;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [points, labels, colorMode, showGrid]);

  // Camera Presets handler
  const setCameraPreset = (preset) => {
    setActiveView(preset);
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    if (preset === 'Driver') {
      camera.position.set(-0.2, 5.8, -12.0);
      controls.target.set(0.0, 1.2, 14.0);
    } else if (preset === 'Top') {
      camera.position.set(0.0, 48.0, 16.0);
      controls.target.set(0.0, 0.0, 16.0);
    } else if (preset === 'Side') {
      camera.position.set(24.0, 4.0, 14.0);
      controls.target.set(0.0, 1.0, 14.0);
    } else if (preset === 'Front') {
      camera.position.set(0.0, 3.5, 36.0);
      controls.target.set(0.0, 1.0, 12.0);
    }
    controls.update();
  };

  return (
    <div className="relative w-full h-[450px] bg-[#09101f] border border-[#172742] rounded-md overflow-hidden shadow-xl flex flex-col">
      {/* Top Header & Toolbar Bar */}
      <div className="bg-[#09101f]/95 border-b border-[#172742] px-3 py-2 flex items-center justify-between text-xs z-10 select-none">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#00d4ff] shadow-[0_0_8px_#00d4ff]" />
          <span className="font-bold text-white text-sm">
            2.5D Semantic Elevation Map <span className="text-[#94a3b8] font-normal text-xs">(Top View + Height)</span>
          </span>
        </div>

        {/* Viewport Presets & Toggles */}
        <div className="flex items-center gap-2">
          {/* Preset Buttons */}
          <div className="flex bg-[#050913] p-0.5 rounded border border-[#172742]">
            {['Driver', 'Top', 'Side', 'Front'].map((p) => (
              <button
                key={p}
                onClick={() => setCameraPreset(p)}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition ${
                  activeView === p
                    ? 'bg-[#2563eb] text-white shadow'
                    : 'text-[#94a3b8] hover:text-white hover:bg-[#172742]'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Color Mode Switcher */}
          <button
            onClick={onToggleColorMode}
            className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-semibold border transition ${
              colorMode === 'semantic'
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
            }`}
          >
            <Eye className="w-3 h-3" />
            <span>{colorMode === 'semantic' ? 'Semantic' : 'Elevation'}</span>
          </button>

          {/* Grid Toggle */}
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`px-2 py-1 rounded text-[11px] font-semibold border transition ${
              showGrid
                ? 'bg-[#00d4ff]/15 text-[#00d4ff] border-[#00d4ff]/40'
                : 'bg-[#0d172a] text-[#64748b] border-[#172742]'
            }`}
          >
            Adaptive Grid
          </button>

          {/* Annotations Toggle */}
          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className={`px-2 py-1 rounded text-[11px] font-semibold border transition ${
              showAnnotations
                ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                : 'bg-[#0d172a] text-[#64748b] border-[#172742]'
            }`}
          >
            Labels
          </button>
        </div>
      </div>

      {/* 3D Canvas Mount */}
      <div ref={mountRef} className="w-full flex-1 relative cursor-grab active:cursor-grabbing">
        {/* Floating Callout Annotations Overlay with Leader Pointer Lines matching Reference Screenshot */}
        {showAnnotations && activeView === 'Driver' && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
            {/* SVG Connecting Leader Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 5 }}>
              {/* 1. Left Wall: Badge bottom-right (22% width, 68px) to Wall target (18% width, 120px) */}
              <line x1="22%" y1="68" x2="19%" y2="125" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="19%" cy="125" r="3.5" fill="#ef4444" />

              {/* 2. Front Vehicle: Badge bottom (51% width, 84px) to Vehicle target (51% width, 135px) */}
              <line x1="51%" y1="84" x2="51%" y2="135" stroke="#d946ef" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="51%" cy="135" r="3.5" fill="#d946ef" />

              {/* 3. Right Tree: Badge bottom-left (76% width, 68px) to Tree canopy (80% width, 115px) */}
              <line x1="76%" y1="68" x2="80%" y2="115" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="80%" cy="115" r="3.5" fill="#10b981" />

              {/* 4. Pedestrian: Badge bottom-left (74% width, 148px) to Pedestrian target (70% width, 185px) */}
              <line x1="74%" y1="148" x2="70%" y2="185" stroke="#eab308" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="70%" cy="185" r="3.5" fill="#eab308" />

              {/* 5. Drivable Road: Badge top (60% width, 320px) to Road target (55% width, 280px) */}
              <line x1="60%" y1="320" x2="55%" y2="280" stroke="#00d4ff" strokeWidth="1.5" strokeDasharray="3 2" />
              <circle cx="55%" cy="280" r="3.5" fill="#00d4ff" />
            </svg>

            {/* 1. Left Wall Callout */}
            <div className="absolute top-5 left-[12%] bg-[#09101f]/95 border border-red-500/90 rounded px-2.5 py-1 text-[11px] shadow-lg shadow-black/60 z-10">
              <div className="text-red-400 font-bold leading-tight">Wall (Non-drivable)</div>
              <div className="text-white text-[10px]">Height: ~2.5 m</div>
            </div>

            {/* 2. Leading Dynamic Vehicle Callout */}
            <div className="absolute top-6 left-[43%] bg-[#09101f]/95 border border-[#d946ef]/90 rounded px-2.5 py-1 text-[11px] shadow-lg shadow-black/60 z-10">
              <div className="text-[#d946ef] font-bold leading-tight">Vehicle (Dynamic)</div>
              <div className="text-white text-[10px]">Height: ~1.5 m</div>
            </div>

            {/* 3. Right Static Tree Callout */}
            <div className="absolute top-5 right-[16%] bg-[#09101f]/95 border border-emerald-500/90 rounded px-2.5 py-1 text-[11px] shadow-lg shadow-black/60 z-10">
              <div className="text-emerald-400 font-bold leading-tight">Tree (Static)</div>
              <div className="text-white text-[10px]">Height: ~5 m</div>
            </div>

            {/* 4. Pedestrian Callout */}
            <div className="absolute top-28 right-[18%] bg-[#09101f]/95 border border-amber-400/90 rounded px-2.5 py-1 text-[11px] shadow-lg shadow-black/60 z-10">
              <div className="text-amber-400 font-bold leading-tight">Pedestrian (Dynamic)</div>
              <div className="text-white text-[10px]">Height: ~1.7 m</div>
            </div>

            {/* 5. Drivable Road Callout */}
            <div className="absolute bottom-16 left-[56%] bg-[#09101f]/95 border border-[#00d4ff]/90 rounded px-2.5 py-1 text-[11px] shadow-lg shadow-black/60 z-10">
              <div className="text-[#00d4ff] font-bold leading-tight">Drivable Road</div>
              <div className="text-white text-[10px]">Height: ~0.0 – 0.5 m</div>
            </div>
          </div>
        )}

        {/* 3D Coordinate Axes Gizmo indicator matching reference screenshot */}
        <div className="absolute bottom-3 left-4 text-[10px] font-mono text-[#cbd5e1] flex flex-col gap-0.5 bg-[#050913]/85 px-2 py-1.5 rounded border border-[#172742] shadow-md select-none pointer-events-none">
          <div className="flex items-center gap-1.5 font-bold">
            <span className="text-[#10b981]">Z (Height) ↑</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#ef4444] font-bold">Y →</span>
            <span className="text-[#00d4ff] font-bold">X ↗</span>
          </div>
        </div>
      </div>
    </div>
  );
}
