import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Eye, Grid, MapPin, Gauge, Layers } from 'lucide-react';
import { CLASS_COLORS } from '../config/constants';

export default function MainLidarViewer({
  points = [],
  labels = [],
  annotations = [],
  colorMode = 'semantic', // 'semantic' | 'elevation'
  onToggleColorMode,
  isPlaying = false,
  dataSource = 'Simulation',
}) {
  const mountRef = useRef(null);
  const controlsRef = useRef(null);
  const cameraRef = useRef(null);

  const [activeView, setActiveView] = useState('Driver');
  const [showGrid, setShowGrid] = useState(true);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [renderFps, setRenderFps] = useState(60);

  // Dynamic projected callout positions (screen X, Y)
  const [callouts2D, setCallouts2D] = useState([]);

  // Camera lerp animation targets
  const targetCamPos = useRef(new THREE.Vector3(-0.2, 5.8, -12.0));
  const targetLookAt = useRef(new THREE.Vector3(0.0, 1.2, 14.0));
  const isTransitioningCam = useRef(false);

  // Refs for dynamic simulation elements
  const dynamicVehiclesRef = useRef([]);
  const dynamicPedestriansRef = useRef([]);
  const dynamicGridPatchRef = useRef(null);
  const lidarBeamRef = useRef(null);
  const isPlayingRef = useRef(isPlaying);

  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight || 450;

    // 1. Scene & Background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050913);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 200);
    camera.position.set(-0.2, 5.8, -12.0);
    cameraRef.current = camera;

    // 3. WebGL Renderer with Anti-Aliasing & ACES Tonemapping
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
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

    const dirLight = new THREE.DirectionalLight(0x00d4ff, 0.6);
    dirLight.position.set(10, 20, -10);
    scene.add(dirLight);

    // 6. Point Cloud Buffer Geometry (GPU Optimized Float32Array)
    let pointCloudGeometry = null;
    let pointCloud = null;

    if (points && points.length > 0) {
      pointCloudGeometry = new THREE.BufferGeometry();
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
          // Turbo elevation gradient (0.0 to 5.0m)
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

      pointCloudGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      pointCloudGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      const pointMaterial = new THREE.PointsMaterial({
        size: 2.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.92,
      });

      pointCloud = new THREE.Points(pointCloudGeometry, pointMaterial);
      scene.add(pointCloud);
    }

    // 7. Multi-Resolution Adaptive Grid Bands on Drivable Surface (Matching Screenshot)
    const gridGroup = new THREE.Group();
    if (showGrid) {
      // Band 1: 0 - 10 m (Fine 5cm - Cyan/Blue)
      const b1PlaneGeo = new THREE.PlaneGeometry(8.4, 18.0);
      const b1PlaneMat = new THREE.MeshBasicMaterial({ color: 0x0055ff, transparent: true, opacity: 0.28, side: THREE.DoubleSide });
      const b1Plane = new THREE.Mesh(b1PlaneGeo, b1PlaneMat);
      b1Plane.rotation.x = -Math.PI / 2;
      b1Plane.position.set(0, 0.02, 1.0);
      gridGroup.add(b1Plane);

      const b1Lines = [];
      for (let x = -4.2; x <= 4.2; x += 0.8) b1Lines.push(x, 0.03, -8.0, x, 0.03, 10.0);
      for (let z = -8.0; z <= 10.0; z += 0.8) b1Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      const b1LinesGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b1Lines, 3));
      gridGroup.add(new THREE.LineSegments(b1LinesGeo, new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.65 })));

      // Band 2: 10 - 25 m (Mid 10cm - Purple/Violet)
      const b2PlaneGeo = new THREE.PlaneGeometry(8.4, 15.0);
      const b2PlaneMat = new THREE.MeshBasicMaterial({ color: 0x7c3aed, transparent: true, opacity: 0.25, side: THREE.DoubleSide });
      const b2Plane = new THREE.Mesh(b2PlaneGeo, b2PlaneMat);
      b2Plane.rotation.x = -Math.PI / 2;
      b2Plane.position.set(0, 0.02, 17.5);
      gridGroup.add(b2Plane);

      const b2Lines = [];
      for (let x = -4.2; x <= 4.2; x += 1.6) b2Lines.push(x, 0.03, 10.0, x, 0.03, 25.0);
      for (let z = 10.0; z <= 25.0; z += 1.6) b2Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      const b2LinesGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b2Lines, 3));
      gridGroup.add(new THREE.LineSegments(b2LinesGeo, new THREE.LineBasicMaterial({ color: 0xa855f7, transparent: true, opacity: 0.55 })));

      // Band 3: 25 - 50 m (Coarse 25cm - Yellow)
      const b3PlaneGeo = new THREE.PlaneGeometry(8.4, 25.0);
      const b3PlaneMat = new THREE.MeshBasicMaterial({ color: 0xd97706, transparent: true, opacity: 0.22, side: THREE.DoubleSide });
      const b3Plane = new THREE.Mesh(b3PlaneGeo, b3PlaneMat);
      b3Plane.rotation.x = -Math.PI / 2;
      b3Plane.position.set(0, 0.02, 37.5);
      gridGroup.add(b3Plane);

      const b3Lines = [];
      for (let x = -4.2; x <= 4.2; x += 2.8) b3Lines.push(x, 0.03, 25.0, x, 0.03, 50.0);
      for (let z = 25.0; z <= 50.0; z += 2.8) b3Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      const b3LinesGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b3Lines, 3));
      gridGroup.add(new THREE.LineSegments(b3LinesGeo, new THREE.LineBasicMaterial({ color: 0xfacc15, transparent: true, opacity: 0.45 })));

      // Band 4: 50 - 100 m (Very Coarse 50cm - Orange/Red)
      const b4PlaneGeo = new THREE.PlaneGeometry(8.4, 50.0);
      const b4PlaneMat = new THREE.MeshBasicMaterial({ color: 0xdc2626, transparent: true, opacity: 0.18, side: THREE.DoubleSide });
      const b4Plane = new THREE.Mesh(b4PlaneGeo, b4PlaneMat);
      b4Plane.rotation.x = -Math.PI / 2;
      b4Plane.position.set(0, 0.02, 75.0);
      gridGroup.add(b4Plane);

      const b4Lines = [];
      for (let x = -4.2; x <= 4.2; x += 4.2) b4Lines.push(x, 0.03, 50.0, x, 0.03, 100.0);
      for (let z = 50.0; z <= 100.0; z += 5.0) b4Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
      const b4LinesGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b4Lines, 3));
      gridGroup.add(new THREE.LineSegments(b4LinesGeo, new THREE.LineBasicMaterial({ color: 0xf87171, transparent: true, opacity: 0.4 })));

      // Dynamic High-Importance Subdivided Grid Patch (Tracks Lead Vehicle)
      const dynamicPatchGeo = new THREE.BufferGeometry();
      const patchLines = [];
      for (let x = -1.8; x <= 1.8; x += 0.4) patchLines.push(x, 0.05, -3.0, x, 0.05, 3.0);
      for (let z = -3.0; z <= 3.0; z += 0.4) patchLines.push(-1.8, 0.05, z, 1.8, 0.05, z);
      dynamicPatchGeo.setAttribute('position', new THREE.Float32BufferAttribute(patchLines, 3));
      const dynamicPatch = new THREE.LineSegments(dynamicPatchGeo, new THREE.LineBasicMaterial({ color: 0x00ffcc, transparent: true, opacity: 0.85 }));
      dynamicPatch.position.set(0.4, 0, 15.5);
      gridGroup.add(dynamicPatch);
      dynamicGridPatchRef.current = dynamicPatch;

      scene.add(gridGroup);
    }

    // 8. 3D Vehicle Models & Kinematic Agents
    // Ego-Vehicle (White car at origin)
    const egoGroup = new THREE.Group();
    const egoBody = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.3, 4.2), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2, metalness: 0.8 }));
    egoBody.position.y = 0.75;
    egoGroup.add(egoBody);

    const egoGlass = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.65, 1.8), new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.75 }));
    egoGlass.position.set(0, 1.25, -0.2);
    egoGroup.add(egoGlass);

    // Roof LiDAR Sensor Dome
    const lidarDome = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.25, 16), new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 }));
    lidarDome.position.set(0, 1.7, 0.2);
    egoGroup.add(lidarDome);

    // LiDAR Laser Scan Sweep Cone (Simulating sensor beam)
    const beamGeo = new THREE.BufferGeometry();
    beamGeo.setAttribute('position', new THREE.Float32BufferAttribute([0, 1.7, 0.2, 0, 0.05, 25.0], 3));
    const lidarBeam = new THREE.Line(beamGeo, new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.35 }));
    egoGroup.add(lidarBeam);
    lidarBeamRef.current = lidarBeam;

    scene.add(egoGroup);

    // Leading dynamic car (Pink/Magenta car matching reference screenshot)
    const leadCarGroup = new THREE.Group();
    const leadCarBody = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.3, 4.2), new THREE.MeshStandardMaterial({ color: 0xd946ef, roughness: 0.3, metalness: 0.7 }));
    leadCarBody.position.y = 0.75;
    leadCarGroup.add(leadCarBody);

    // Bounding Box wireframe for AI Object Detection
    const leadBoxGeo = new THREE.BoxGeometry(2.0, 1.6, 4.5);
    const leadBoxEdges = new THREE.EdgesGeometry(leadBoxGeo);
    const leadBoxLine = new THREE.LineSegments(leadBoxEdges, new THREE.LineBasicMaterial({ color: 0xd946ef, transparent: true, opacity: 0.8 }));
    leadBoxLine.position.y = 0.8;
    leadCarGroup.add(leadBoxLine);

    leadCarGroup.position.set(0.4, 0, 15.5);
    scene.add(leadCarGroup);

    // Far vehicle ahead (at 32m)
    const farCar = new THREE.Mesh(new THREE.BoxGeometry(1.8, 1.3, 4.2), new THREE.MeshStandardMaterial({ color: 0xd946ef, roughness: 0.3, metalness: 0.7 }));
    farCar.position.set(-1.6, 0.75, 32.0);
    scene.add(farCar);

    dynamicVehiclesRef.current = [leadCarGroup, farCar];

    // Dynamic Pedestrian Markers
    const pedGroup = new THREE.Group();
    const pedBody = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 1.5, 8), new THREE.MeshStandardMaterial({ color: 0xeab308, roughness: 0.4 }));
    pedBody.position.y = 0.75;
    pedGroup.add(pedBody);
    const pedHead = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfacc15 }));
    pedHead.position.y = 1.65;
    pedGroup.add(pedHead);
    pedGroup.position.set(5.2, 0, 18.0);
    scene.add(pedGroup);
    dynamicPedestriansRef.current = [pedGroup];

    // 9. Coordinate Axes Gizmo (Z Height Green, Y Lateral Red, X Forward Blue)
    const axesGroup = new THREE.Group();
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0, 0), 2.2, 0x00d4ff, 0.4, 0.2)); // X
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 2.2, 0xef4444, 0.4, 0.2)); // Y
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 0), 2.2, 0x10b981, 0.4, 0.2)); // Z
    axesGroup.position.set(-6.5, 0.2, -6.0);
    scene.add(axesGroup);

    // 10. Animation Render Loop (Continuous Simulation & Projected Screen-Space Callouts)
    let animId;
    let lastTime = performance.now();
    let frameCounter = 0;
    let fpsTimer = performance.now();
    let simTime = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);

      const now = performance.now();
      const dt = (now - lastTime) / 1000;
      lastTime = now;

      // Instantaneous WebGL Frame Rate
      frameCounter++;
      if (now - fpsTimer >= 1000) {
        setRenderFps(frameCounter);
        frameCounter = 0;
        fpsTimer = now;
      }

      // Smooth Camera Lerping between Presets
      if (isTransitioningCam.current) {
        camera.position.lerp(targetCamPos.current, 0.08);
        controls.target.lerp(targetLookAt.current, 0.08);
        if (camera.position.distanceTo(targetCamPos.current) < 0.05) {
          isTransitioningCam.current = false;
        }
      }

      // Dynamic Simulation Kinematics (When isPlaying is true)
      if (isPlayingRef.current) {
        simTime += dt;

        // Animate Lead Vehicle forward along road (Z axis)
        const leadZ = 14.0 + Math.sin(simTime * 0.8) * 6.0;
        leadCarGroup.position.z = leadZ;

        // Dynamic fine grid patch tracks lead car
        if (dynamicGridPatchRef.current) {
          dynamicGridPatchRef.current.position.z = leadZ;
        }

        // Animate Pedestrian walking along sidewalk
        const pedZ = 16.0 + Math.sin(simTime * 0.6) * 4.0;
        pedGroup.position.z = pedZ;

        // Subtle sensor beam sweep
        if (lidarBeamRef.current) {
          const sweepAngle = Math.sin(simTime * 4.0) * 0.25;
          lidarBeamRef.current.rotation.y = sweepAngle;
        }
      }

      controls.update();
      renderer.render(scene, camera);

      // Project 3D callout targets to 2D screen coordinates
      if (showAnnotations) {
        const targets = [
          { id: 'wall', label: 'Wall (Non-drivable)', sub: 'Height: ~2.5 m', color: '#ef4444', pos3D: new THREE.Vector3(-7.5, 2.5, 12.0) },
          { id: 'vehicle', label: 'Vehicle (Dynamic)', sub: 'Height: ~1.5 m', color: '#d946ef', pos3D: new THREE.Vector3(leadCarGroup.position.x, 1.5, leadCarGroup.position.z) },
          { id: 'tree', label: 'Tree (Static)', sub: 'Height: ~5 m', color: '#10b981', pos3D: new THREE.Vector3(8.0, 4.2, 22.0) },
          { id: 'pedestrian', label: 'Pedestrian (Dynamic)', sub: 'Height: ~1.7 m', color: '#eab308', pos3D: new THREE.Vector3(pedGroup.position.x, 1.7, pedGroup.position.z) },
          { id: 'road', label: 'Drivable Road', sub: 'Height: ~0.0 – 0.5 m', color: '#00d4ff', pos3D: new THREE.Vector3(0.0, 0.1, 6.0) },
        ];

        const projected = targets.map((t) => {
          const v = t.pos3D.clone();
          v.project(camera);
          const x = (v.x * 0.5 + 0.5) * width;
          const y = (-(v.y * 0.5) + 0.5) * height;
          const isBehind = v.z > 1.0;
          return { ...t, screenX: x, screenY: y, visible: !isBehind && x > 20 && x < width - 20 && y > 20 && y < height - 20 };
        });

        setCallouts2D(projected);
      }
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
      if (pointCloudGeometry) pointCloudGeometry.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [points, labels, colorMode, showGrid]);

  // Smooth Camera Presets Handler
  const setCameraPreset = (preset) => {
    setActiveView(preset);
    isTransitioningCam.current = true;

    if (preset === 'Driver') {
      targetCamPos.current.set(-0.2, 5.8, -12.0);
      targetLookAt.current.set(0.0, 1.2, 14.0);
    } else if (preset === 'Top') {
      targetCamPos.current.set(0.0, 52.0, 16.0);
      targetLookAt.current.set(0.0, 0.0, 16.0);
    } else if (preset === 'Side') {
      targetCamPos.current.set(24.0, 4.0, 14.0);
      targetLookAt.current.set(0.0, 1.0, 14.0);
    } else if (preset === 'Front') {
      targetCamPos.current.set(0.0, 3.5, 38.0);
      targetLookAt.current.set(0.0, 1.0, 12.0);
    }
  };

  return (
    <div className="relative w-full h-[450px] bg-[#09101f] border border-[#172742] rounded-md overflow-hidden shadow-xl flex flex-col">
      {/* Top Header & Toolbar Bar */}
      <div className="bg-[#09101f]/95 border-b border-[#172742] px-3 py-2 flex items-center justify-between text-xs z-20 select-none">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#00d4ff] shadow-[0_0_8px_#00d4ff]" />
          <span className="font-bold text-white text-sm">
            2.5D Semantic Elevation Map <span className="text-[#94a3b8] font-normal text-xs">(Top View + Height)</span>
          </span>
        </div>

        {/* Viewport Presets & Controls */}
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

          {/* Adaptive Grid Toggle */}
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

          {/* Labels Toggle */}
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
        {/* Dynamic Screen-Space Projected Callouts Overlay with SVG Leader Lines */}
        {showAnnotations && activeView === 'Driver' && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden select-none z-10">
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {callouts2D.map(
                (c) =>
                  c.visible && (
                    <g key={`leader-${c.id}`}>
                      {/* Leader Pointer Line */}
                      <line
                        x1={c.screenX}
                        y1={c.screenY - 35}
                        x2={c.screenX}
                        y2={c.screenY}
                        stroke={c.color}
                        strokeWidth="1.5"
                        strokeDasharray="3 2"
                      />
                      {/* Anchor Circle Dot at 3D Entity Position */}
                      <circle cx={c.screenX} cy={c.screenY} r="3.5" fill={c.color} />
                    </g>
                  )
              )}
            </svg>

            {/* Projected Badges */}
            {callouts2D.map(
              (c) =>
                c.visible && (
                  <div
                    key={`badge-${c.id}`}
                    className="absolute bg-[#09101f]/95 border rounded px-2 py-0.8 text-[11px] shadow-lg shadow-black/60 pointer-events-auto"
                    style={{
                      left: `${c.screenX}px`,
                      top: `${c.screenY - 42}px`,
                      transform: 'translate(-50%, -100%)',
                      borderColor: `${c.color}dd`,
                    }}
                  >
                    <div className="font-bold leading-tight" style={{ color: c.color }}>
                      {c.label}
                    </div>
                    <div className="text-white text-[10px] leading-none mt-0.5">{c.sub}</div>
                  </div>
                )
            )}
          </div>
        )}

        {/* Viewport HUD Telemetry: GPU FPS, Provenance, Coordinates */}
        <div className="absolute top-2 left-3 flex items-center gap-2 pointer-events-none z-10">
          <div className="flex items-center gap-1.5 px-2 py-0.8 rounded bg-[#050913]/90 border border-[#172742] text-[10px] font-mono text-[#38bdf8]">
            <Gauge className="w-3 h-3 text-[#10b981]" />
            <span>WebGL:</span>
            <span className="text-white font-bold">{renderFps} FPS</span>
          </div>

          <div
            className={`px-2 py-0.8 rounded border text-[10px] font-mono font-semibold ${
              dataSource === 'FastAPI'
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-cyan-500/10 border-cyan-500/30 text-[#38bdf8]'
            }`}
          >
            {dataSource === 'FastAPI' ? 'PROVENANCE: MEASURED (FASTAPI)' : 'PROVENANCE: SIMULATION (THREE.JS GPU)'}
          </div>
        </div>

        {/* 3D Coordinate Axes Gizmo indicator matching reference screenshot */}
        <div className="absolute bottom-3 left-4 text-[10px] font-mono text-[#cbd5e1] flex flex-col gap-0.5 bg-[#050913]/85 px-2 py-1.5 rounded border border-[#172742] shadow-md select-none pointer-events-none z-10">
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
