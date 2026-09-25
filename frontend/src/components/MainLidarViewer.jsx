import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Eye, Gauge } from 'lucide-react';
import { CLASS_COLORS } from '../config/constants';

// Screen-space 3D projected callout targets
const TARGET_SPECS = [
  { id: 'wall', label: 'Left Wall', sub: 'Non-drivable', color: '#ef4444' },
  { id: 'vehicle', label: 'Front Vehicle', sub: 'Dynamic', color: '#d946ef' },
  { id: 'tree', label: 'Right Tree', sub: 'Static Obstacle', color: '#10b981' },
  { id: 'pedestrian', label: 'Pedestrian', sub: 'Sidewalk (Active)', color: '#eab308' },
  { id: 'road', label: 'Road Surface', sub: 'Drivable Corridor', color: '#38bdf8' },
];

export default function MainLidarViewer({
  points = [],
  labels = [],
  annotations = [],
  colorMode = 'semantic',
  onToggleColorMode,
  isPlaying = false,
  dataSource = 'Simulation',
}) {
  const mountRef = useRef(null);
  const [activeView, setActiveView] = useState('Driver');
  const [showGrid, setShowGrid] = useState(true);
  const [showAnnotations, setShowAnnotations] = useState(true);

  // Persistent WebGL refs
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const pointCloudRef = useRef(null);
  const pointCloudGeometryRef = useRef(null);
  const gridGroupRef = useRef(null);
  const dynamicVehiclesRef = useRef([]);
  const dynamicPedestriansRef = useRef([]);
  const dynamicGridPatchRef = useRef(null);
  const lidarBeamRef = useRef(null);

  // DOM direct-transform refs
  const fpsTextRef = useRef(null);
  const badgeRefs = useRef({});
  const lineRefs = useRef({});
  const dotRefs = useRef({});

  // Camera lerp animation targets
  const targetCamPos = useRef(new THREE.Vector3(-0.2, 5.8, -12.0));
  const targetLookAt = useRef(new THREE.Vector3(0.0, 1.2, 14.0));
  const isTransitioningCam = useRef(false);

  // Active state refs for 60 FPS animation loop
  const isPlayingRef = useRef(isPlaying);
  const showAnnotationsRef = useRef(showAnnotations);
  const pointsRef = useRef(points);
  const labelsRef = useRef(labels);
  const colorModeRef = useRef(colorMode);

  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  useEffect(() => {
    pointsRef.current = points;
    labelsRef.current = labels;
    colorModeRef.current = colorMode;
  }, [points, labels, colorMode]);

  useEffect(() => {
    showAnnotationsRef.current = showAnnotations;
    if (!showAnnotations) {
      TARGET_SPECS.forEach((s) => {
        if (badgeRefs.current[s.id]) badgeRefs.current[s.id].style.display = 'none';
        if (lineRefs.current[s.id]) lineRefs.current[s.id].style.display = 'none';
        if (dotRefs.current[s.id]) dotRefs.current[s.id].style.display = 'none';
      });
    }
  }, [showAnnotations]);

  // Fast GPU BufferAttribute update helper (Zero scene rebuild, zero GC churn)
  const updatePointCloudData = (pts, lbls, mode) => {
    if (!sceneRef.current || !pts || pts.length === 0) return;
    const count = pts.length;
    let geom = pointCloudGeometryRef.current;
    let pc = pointCloudRef.current;

    // Check if buffer needs re-allocation due to point count change
    if (!geom || geom.attributes?.position?.count !== count) {
      if (geom) geom.dispose();
      geom = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);
      geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      pointCloudGeometryRef.current = geom;

      if (!pc) {
        const pointMaterial = new THREE.PointsMaterial({
          size: 2.4,
          vertexColors: true,
          transparent: true,
          opacity: 0.92,
        });
        pc = new THREE.Points(geom, pointMaterial);
        pointCloudRef.current = pc;
        sceneRef.current.add(pc);
      } else {
        pc.geometry = geom;
      }
    }

    const posAttr = geom.attributes.position;
    const colAttr = geom.attributes.color;
    const positions = posAttr.array;
    const colors = colAttr.array;
    const colorObj = new THREE.Color();

    for (let i = 0; i < count; i++) {
      const pt = pts[i];
      positions[i * 3] = pt[1];
      positions[i * 3 + 1] = pt[2];
      positions[i * 3 + 2] = pt[0];

      if (mode === 'elevation') {
        const normZ = Math.max(0, Math.min(1, pt[2] / 4.8));
        colorObj.setHSL(0.65 - normZ * 0.65, 0.95, 0.52);
      } else {
        const lbl = lbls && lbls[i] !== undefined ? lbls[i] : 0;
        const hex = CLASS_COLORS[lbl] || '#64748b';
        colorObj.set(hex);
      }

      colors[i * 3] = colorObj.r;
      colors[i * 3 + 1] = colorObj.g;
      colors[i * 3 + 2] = colorObj.b;
    }

    posAttr.needsUpdate = true;
    colAttr.needsUpdate = true;
  };

  // Sync point cloud buffer on data or mode change
  useEffect(() => {
    updatePointCloudData(points, labels, colorMode);
  }, [points, labels, colorMode]);

  // Sync adaptive grid visibility instantaneously
  useEffect(() => {
    if (gridGroupRef.current) {
      gridGroupRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // Initialize WebGL Scene, Cameras, Lights & Animation Loop ONCE on mount
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let width = container.clientWidth || 800;
    let height = container.clientHeight || 450;

    // 1. Scene & Background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050913);
    sceneRef.current = scene;

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 200);
    camera.position.set(-0.2, 5.8, -12.0);
    cameraRef.current = camera;

    // 3. WebGL Renderer with High Performance & Touch Action
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.domElement.style.touchAction = 'none'; // Critical for smooth mobile touch control
    rendererRef.current = renderer;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. Orbit Controls with Damping and Mobile Gestures
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.rotateSpeed = 0.75;
    controls.zoomSpeed = 0.9;
    controls.panSpeed = 0.75;
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    controls.target.set(0.0, 1.2, 14.0);
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00d4ff, 0.6);
    dirLight.position.set(10, 20, -10);
    scene.add(dirLight);

    // 6. Multi-Resolution Adaptive Grid Bands
    const gridGroup = new THREE.Group();
    gridGroup.visible = showGrid;
    gridGroupRef.current = gridGroup;

    // Band 1: 0 - 10 m (Fine 5cm - Cyan/Blue)
    const b1Plane = new THREE.Mesh(
      new THREE.PlaneGeometry(8.4, 18.0),
      new THREE.MeshBasicMaterial({ color: 0x0055ff, transparent: true, opacity: 0.28, side: THREE.DoubleSide })
    );
    b1Plane.rotation.x = -Math.PI / 2;
    b1Plane.position.set(0, 0.02, 1.0);
    gridGroup.add(b1Plane);

    const b1Lines = [];
    for (let x = -4.2; x <= 4.2; x += 0.8) b1Lines.push(x, 0.03, -8.0, x, 0.03, 10.0);
    for (let z = -8.0; z <= 10.0; z += 0.8) b1Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
    gridGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b1Lines, 3)),
      new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.65 })
    ));

    // Band 2: 10 - 25 m (Mid 10cm - Purple/Violet)
    const b2Plane = new THREE.Mesh(
      new THREE.PlaneGeometry(8.4, 15.0),
      new THREE.MeshBasicMaterial({ color: 0x7c3aed, transparent: true, opacity: 0.25, side: THREE.DoubleSide })
    );
    b2Plane.rotation.x = -Math.PI / 2;
    b2Plane.position.set(0, 0.02, 17.5);
    gridGroup.add(b2Plane);

    const b2Lines = [];
    for (let x = -4.2; x <= 4.2; x += 1.6) b2Lines.push(x, 0.03, 10.0, x, 0.03, 25.0);
    for (let z = 10.0; z <= 25.0; z += 1.6) b2Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
    gridGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b2Lines, 3)),
      new THREE.LineBasicMaterial({ color: 0xa855f7, transparent: true, opacity: 0.55 })
    ));

    // Band 3: 25 - 50 m (Coarse 25cm - Yellow)
    const b3Plane = new THREE.Mesh(
      new THREE.PlaneGeometry(8.4, 25.0),
      new THREE.MeshBasicMaterial({ color: 0xd97706, transparent: true, opacity: 0.22, side: THREE.DoubleSide })
    );
    b3Plane.rotation.x = -Math.PI / 2;
    b3Plane.position.set(0, 0.02, 37.5);
    gridGroup.add(b3Plane);

    const b3Lines = [];
    for (let x = -4.2; x <= 4.2; x += 2.8) b3Lines.push(x, 0.03, 25.0, x, 0.03, 50.0);
    for (let z = 25.0; z <= 50.0; z += 2.8) b3Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
    gridGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b3Lines, 3)),
      new THREE.LineBasicMaterial({ color: 0xfacc15, transparent: true, opacity: 0.45 })
    ));

    // Band 4: 50 - 100 m (Very Coarse 50cm - Orange/Red)
    const b4Plane = new THREE.Mesh(
      new THREE.PlaneGeometry(8.4, 50.0),
      new THREE.MeshBasicMaterial({ color: 0xdc2626, transparent: true, opacity: 0.18, side: THREE.DoubleSide })
    );
    b4Plane.rotation.x = -Math.PI / 2;
    b4Plane.position.set(0, 0.02, 75.0);
    gridGroup.add(b4Plane);

    const b4Lines = [];
    for (let x = -4.2; x <= 4.2; x += 4.2) b4Lines.push(x, 0.03, 50.0, x, 0.03, 100.0);
    for (let z = 50.0; z <= 100.0; z += 5.0) b4Lines.push(-4.2, 0.03, z, 4.2, 0.03, z);
    gridGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(b4Lines, 3)),
      new THREE.LineBasicMaterial({ color: 0xf87171, transparent: true, opacity: 0.4 })
    ));

    // Dynamic High-Importance Subdivided Grid Patch
    const patchLines = [];
    for (let x = -1.8; x <= 1.8; x += 0.4) patchLines.push(x, 0.05, -3.0, x, 0.05, 3.0);
    for (let z = -3.0; z <= 3.0; z += 0.4) patchLines.push(-1.8, 0.05, z, 1.8, 0.05, z);
    const dynamicPatch = new THREE.LineSegments(
      new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(patchLines, 3)),
      new THREE.LineBasicMaterial({ color: 0x00ffcc, transparent: true, opacity: 0.85 })
    );
    dynamicPatch.position.set(0.4, 0, 15.5);
    gridGroup.add(dynamicPatch);
    dynamicGridPatchRef.current = dynamicPatch;

    scene.add(gridGroup);

    // 7. 3D Vehicle Models & Kinematic Agents
    const egoGroup = new THREE.Group();
    const egoBody = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 1.3, 4.2),
      new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2, metalness: 0.8 })
    );
    egoBody.position.y = 0.75;
    egoGroup.add(egoBody);

    const egoGlass = new THREE.Mesh(
      new THREE.BoxGeometry(1.6, 0.65, 1.8),
      new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.75 })
    );
    egoGlass.position.set(0, 1.25, -0.2);
    egoGroup.add(egoGlass);

    const lidarDome = new THREE.Mesh(
      new THREE.CylinderGeometry(0.2, 0.2, 0.25, 16),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 })
    );
    lidarDome.position.set(0, 1.7, 0.2);
    egoGroup.add(lidarDome);

    const beamGeo = new THREE.BufferGeometry().setAttribute(
      'position',
      new THREE.Float32BufferAttribute([0, 1.7, 0.2, 0, 0.05, 25.0], 3)
    );
    const lidarBeam = new THREE.Line(
      beamGeo,
      new THREE.LineBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.35 })
    );
    egoGroup.add(lidarBeam);
    lidarBeamRef.current = lidarBeam;
    scene.add(egoGroup);

    // Leading dynamic vehicle with 3D bounding box
    const leadCarGroup = new THREE.Group();
    const leadCarBody = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 1.3, 4.2),
      new THREE.MeshStandardMaterial({ color: 0xd946ef, roughness: 0.3, metalness: 0.7 })
    );
    leadCarBody.position.y = 0.75;
    leadCarGroup.add(leadCarBody);

    const leadBoxEdges = new THREE.EdgesGeometry(new THREE.BoxGeometry(2.0, 1.6, 4.5));
    const leadBoxLine = new THREE.LineSegments(
      leadBoxEdges,
      new THREE.LineBasicMaterial({ color: 0xd946ef, transparent: true, opacity: 0.8 })
    );
    leadBoxLine.position.y = 0.8;
    leadCarGroup.add(leadBoxLine);
    leadCarGroup.position.set(0.4, 0, 15.5);
    scene.add(leadCarGroup);

    // Far car ahead
    const farCar = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 1.3, 4.2),
      new THREE.MeshStandardMaterial({ color: 0xd946ef, roughness: 0.3, metalness: 0.7 })
    );
    farCar.position.set(-1.6, 0.75, 32.0);
    scene.add(farCar);

    // Oncoming car in opposite lane
    const oncomingCar = new THREE.Group();
    const onCarBody = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 1.25, 4.2),
      new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.25, metalness: 0.8 })
    );
    onCarBody.position.y = 0.72;
    oncomingCar.add(onCarBody);
    const hLight1 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 8), new THREE.MeshBasicMaterial({ color: 0xfef08a }));
    hLight1.position.set(-0.6, 0.65, -2.1);
    oncomingCar.add(hLight1);
    const hLight2 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 8), new THREE.MeshBasicMaterial({ color: 0xfef08a }));
    hLight2.position.set(0.6, 0.65, -2.1);
    oncomingCar.add(hLight2);
    oncomingCar.position.set(-2.0, 0, 28.0);
    scene.add(oncomingCar);

    dynamicVehiclesRef.current = [leadCarGroup, farCar, oncomingCar];

    // Dynamic Pedestrian 1 (Right sidewalk)
    const pedGroup = new THREE.Group();
    const pedBody = new THREE.Mesh(
      new THREE.CylinderGeometry(0.25, 0.25, 1.5, 8),
      new THREE.MeshStandardMaterial({ color: 0xeab308, roughness: 0.4 })
    );
    pedBody.position.y = 0.75;
    pedGroup.add(pedBody);
    const pedHead = new THREE.Mesh(new THREE.SphereGeometry(0.2, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfacc15 }));
    pedHead.position.y = 1.65;
    pedGroup.add(pedHead);
    pedGroup.position.set(5.2, 0, 18.0);
    scene.add(pedGroup);

    // Pedestrian 2 (Left sidewalk)
    const ped2Group = new THREE.Group();
    const ped2Body = new THREE.Mesh(
      new THREE.CylinderGeometry(0.24, 0.24, 1.45, 8),
      new THREE.MeshStandardMaterial({ color: 0x06b6d4, roughness: 0.4 })
    );
    ped2Body.position.y = 0.72;
    ped2Group.add(ped2Body);
    const ped2Head = new THREE.Mesh(new THREE.SphereGeometry(0.19, 8, 8), new THREE.MeshStandardMaterial({ color: 0xfacc15 }));
    ped2Head.position.y = 1.6;
    ped2Group.add(ped2Head);
    ped2Group.position.set(-5.3, 0.16, 26.0);
    scene.add(ped2Group);

    dynamicPedestriansRef.current = [pedGroup, ped2Group];

    // 8. 3D Architectural Buildings along the Left Boulevard
    const buildingsGroup = new THREE.Group();
    const buildingMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.75,
      metalness: 0.35,
    });
    const glassMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.65,
    });
    const warmWindowMat = new THREE.MeshBasicMaterial({
      color: 0xfef08a,
      transparent: true,
      opacity: 0.75,
    });
    const concreteWallMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      roughness: 0.85,
    });

    const createBuilding = (x, z, width, height, depth) => {
      const bGroup = new THREE.Group();
      const body = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), buildingMat);
      body.position.set(x, height / 2, z);
      bGroup.add(body);

      const numFloors = Math.floor(height / 2.4);
      const numCols = Math.floor(depth / 2.2);
      const facadeX = x + width / 2 + 0.02;

      for (let floor = 1; floor < numFloors; floor++) {
        const floorY = floor * 2.4;
        for (let col = 0; col < numCols; col++) {
          const winZ = z - depth / 2 + (col + 0.5) * (depth / numCols);
          const isWarm = (floor + col) % 3 === 0;
          const win = new THREE.Mesh(
            new THREE.PlaneGeometry(1.2, 1.1),
            isWarm ? warmWindowMat : glassMat
          );
          win.rotation.y = Math.PI / 2;
          win.position.set(facadeX, floorY, winZ);
          bGroup.add(win);
        }
      }

      // Rooftop HVAC & Red Beacon
      const roofHvac = new THREE.Mesh(
        new THREE.BoxGeometry(width * 0.45, 1.2, depth * 0.45),
        new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.6 })
      );
      roofHvac.position.set(x, height + 0.6, z);
      bGroup.add(roofHvac);

      const beacon = new THREE.Mesh(
        new THREE.SphereGeometry(0.18, 8, 8),
        new THREE.MeshBasicMaterial({ color: 0xef4444 })
      );
      beacon.position.set(x, height + 1.8, z);
      bGroup.add(beacon);

      return bGroup;
    };

    buildingsGroup.add(createBuilding(-14.0, 14.0, 10.0, 14.0, 16.0));
    buildingsGroup.add(createBuilding(-15.0, 34.0, 11.0, 18.0, 18.0));
    buildingsGroup.add(createBuilding(-13.5, -4.0, 9.0, 8.5, 14.0));
    buildingsGroup.add(createBuilding(-15.5, 54.0, 11.0, 13.0, 16.0));

    // Continuous Perimeter Safety Barrier / Wall (at X = -6.8m)
    const wallMesh = new THREE.Mesh(new THREE.BoxGeometry(0.35, 1.35, 75.0), concreteWallMat);
    wallMesh.position.set(-6.8, 0.68, 27.5);
    buildingsGroup.add(wallMesh);

    const wallEdges = new THREE.EdgesGeometry(new THREE.BoxGeometry(0.45, 1.5, 75.0));
    const wallLine = new THREE.LineSegments(
      wallEdges,
      new THREE.LineBasicMaterial({ color: 0xef4444, transparent: true, opacity: 0.7 })
    );
    wallLine.position.set(-6.8, 0.75, 27.5);
    buildingsGroup.add(wallLine);

    scene.add(buildingsGroup);

    // 9. 3D Lush Trees with Multi-Tier Foliage Canopies
    const treesGroup = new THREE.Group();
    const treeTrunkMat = new THREE.MeshStandardMaterial({ color: 0x4a2e1b, roughness: 0.9 });
    const leafMats = [
      new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.45 }),
      new THREE.MeshStandardMaterial({ color: 0x059669, roughness: 0.5 }),
      new THREE.MeshStandardMaterial({ color: 0x34d399, roughness: 0.4 }),
    ];

    const treeConfigs = [
      { x: 8.0, z: 8.0, trunkH: 2.4, crownR: 1.9 },
      { x: 8.2, z: 22.0, trunkH: 2.8, crownR: 2.2 },
      { x: 7.8, z: 36.0, trunkH: 2.2, crownR: 1.8 },
      { x: 8.0, z: 48.0, trunkH: 2.5, crownR: 2.0 },
    ];

    const animatedTreeCanopies = [];

    treeConfigs.forEach(({ x, z, trunkH, crownR }, idx) => {
      const tGroup = new THREE.Group();
      tGroup.position.set(x, 0, z);

      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.35, trunkH, 10), treeTrunkMat);
      trunk.position.y = trunkH / 2;
      tGroup.add(trunk);

      const canopyGroup = new THREE.Group();
      canopyGroup.position.y = trunkH;

      const centerCrown = new THREE.Mesh(new THREE.DodecahedronGeometry(crownR, 1), leafMats[idx % 3]);
      centerCrown.position.y = crownR * 0.7;
      canopyGroup.add(centerCrown);

      const clusterOffsets = [
        [0.8, 0.5, 0.6, 0.75],
        [-0.7, 0.6, -0.6, 0.7],
        [0.6, 0.9, -0.7, 0.65],
        [-0.6, 0.8, 0.7, 0.65],
        [0.0, crownR * 1.1, 0.0, 0.8],
      ];

      clusterOffsets.forEach(([ox, oy, oz, scale], cIdx) => {
        const leafBall = new THREE.Mesh(new THREE.DodecahedronGeometry(crownR * scale, 1), leafMats[(idx + cIdx) % 3]);
        leafBall.position.set(ox, oy, oz);
        canopyGroup.add(leafBall);
      });

      tGroup.add(canopyGroup);
      animatedTreeCanopies.push(canopyGroup);
      treesGroup.add(tGroup);
    });

    scene.add(treesGroup);

    // 10. 3D Street Lamp Posts along sidewalks
    const streetLampGroup = new THREE.Group();
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.3 });
    const luminaireMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

    const lampPositions = [
      { x: -4.8, z: 5.0, armDir: 1 },
      { x: 4.8, z: 20.0, armDir: -1 },
      { x: -4.8, z: 35.0, armDir: 1 },
      { x: 4.8, z: 50.0, armDir: -1 },
    ];

    lampPositions.forEach(({ x, z, armDir }) => {
      const lGroup = new THREE.Group();
      lGroup.position.set(x, 0, z);

      const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 4.4, 8), poleMat);
      mast.position.y = 2.2;
      lGroup.add(mast);

      const arm = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.07, 0.07), poleMat);
      arm.position.set(armDir * 0.6, 4.35, 0);
      lGroup.add(arm);

      const lampHead = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.08, 0.18), poleMat);
      lampHead.position.set(armDir * 1.2, 4.3, 0);
      lGroup.add(lampHead);

      const bulb = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.14), luminaireMat);
      bulb.rotation.x = Math.PI / 2;
      bulb.position.set(armDir * 1.2, 4.25, 0);
      lGroup.add(bulb);

      streetLampGroup.add(lGroup);
    });

    scene.add(streetLampGroup);

    // 11. Curbs, Sidewalks & Center Lane Markings
    const sidewalkMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 });
    const curbMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.8 });

    const leftSW = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.16, 75.0), sidewalkMat);
    leftSW.position.set(-5.4, 0.08, 27.5);
    scene.add(leftSW);

    const rightSW = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.16, 75.0), sidewalkMat);
    rightSW.position.set(5.4, 0.08, 27.5);
    scene.add(rightSW);

    const leftCurb = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.22, 75.0), curbMat);
    leftCurb.position.set(-4.2, 0.11, 27.5);
    scene.add(leftCurb);

    const rightCurb = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.22, 75.0), curbMat);
    rightCurb.position.set(4.2, 0.11, 27.5);
    scene.add(rightCurb);

    const laneLines = [];
    for (let lz = -10.0; lz <= 65.0; lz += 4.0) {
      laneLines.push(0, 0.04, lz, 0, 0.04, lz + 2.0);
    }
    const laneGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(laneLines, 3));
    scene.add(new THREE.LineSegments(laneGeo, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85 })));

    // 12. 3D Axes Gizmo
    const axesGroup = new THREE.Group();
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0, 0), 2.2, 0x00d4ff, 0.4, 0.2));
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 2.2, 0xef4444, 0.4, 0.2));
    axesGroup.add(new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 0), 2.2, 0x10b981, 0.4, 0.2));
    axesGroup.position.set(-6.5, 0.2, -6.0);
    scene.add(axesGroup);

    // Pre-allocated vector cache for zero-GC projection
    const target3D = {
      wall: new THREE.Vector3(-7.5, 2.5, 12.0),
      vehicle: new THREE.Vector3(0.4, 1.5, 15.5),
      tree: new THREE.Vector3(8.0, 4.2, 22.0),
      pedestrian: new THREE.Vector3(5.2, 1.7, 18.0),
      road: new THREE.Vector3(0.0, 0.1, 6.0),
    };
    const projVec = new THREE.Vector3();

    // Initial point cloud population
    updatePointCloudData(pointsRef.current, labelsRef.current, colorModeRef.current);

    // 9. 60 FPS Render Loop (ZERO REACT STATE SETTERS INSIDE)
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

      // Update FPS directly on DOM text
      frameCounter++;
      if (now - fpsTimer >= 1000) {
        if (fpsTextRef.current) {
          fpsTextRef.current.textContent = `${frameCounter} FPS`;
        }
        frameCounter = 0;
        fpsTimer = now;
      }

      // Smooth Camera Lerping between Presets
      if (isTransitioningCam.current) {
        camera.position.lerp(targetCamPos.current, 0.08);
        controls.target.lerp(targetLookAt.current, 0.08);
        if (camera.position.distanceTo(targetCamPos.current) < 0.04) {
          isTransitioningCam.current = false;
        }
      }

      // Dynamic Kinematics
      if (isPlayingRef.current) {
        simTime += dt;

        // Animate Lead Vehicle forward along road (Z axis)
        const leadZ = 14.0 + Math.sin(simTime * 0.8) * 6.0;
        leadCarGroup.position.z = leadZ;
        target3D.vehicle.z = leadZ;

        // Dynamic fine grid patch tracks lead car
        if (dynamicGridPatchRef.current) {
          dynamicGridPatchRef.current.position.z = leadZ;
        }

        // Animate Pedestrian walking along sidewalk
        const pedZ = 16.0 + Math.sin(simTime * 0.6) * 4.0;
        pedGroup.position.z = pedZ;
        target3D.pedestrian.z = pedZ;

        // Animate Oncoming Vehicle along left lane
        if (oncomingCar) {
          const onZ = 30.0 - Math.sin(simTime * 0.75) * 9.0;
          oncomingCar.position.z = onZ;
        }

        // Animate second pedestrian along left sidewalk
        if (ped2Group) {
          const ped2Z = 24.0 + Math.cos(simTime * 0.55) * 3.8;
          ped2Group.position.z = ped2Z;
        }

        // Animate lush trees gentle organic wind sway
        if (animatedTreeCanopies) {
          animatedTreeCanopies.forEach((canopy, idx) => {
            canopy.rotation.z = Math.sin(simTime * 1.8 + idx * 1.3) * 0.028;
            canopy.rotation.x = Math.cos(simTime * 1.3 + idx * 0.9) * 0.022;
          });
        }

        // Sensor beam sweep
        if (lidarBeamRef.current) {
          lidarBeamRef.current.rotation.y = Math.sin(simTime * 4.0) * 0.25;
        }
      }

      controls.update();
      renderer.render(scene, camera);

      // Fast Direct DOM transforms for projected callouts (ZERO React state lag)
      if (showAnnotationsRef.current) {
        for (let i = 0; i < TARGET_SPECS.length; i++) {
          const spec = TARGET_SPECS[i];
          const badgeEl = badgeRefs.current[spec.id];
          const lineEl = lineRefs.current[spec.id];
          const dotEl = dotRefs.current[spec.id];

          if (!badgeEl) continue;

          projVec.copy(target3D[spec.id]);
          projVec.project(camera);

          const isBehind = projVec.z > 1.0;
          const x = (projVec.x * 0.5 + 0.5) * width;
          const y = (-(projVec.y * 0.5) + 0.5) * height;

          if (!isBehind && x > 25 && x < width - 25 && y > 25 && y < height - 25) {
            badgeEl.style.display = 'block';
            badgeEl.style.transform = `translate3d(${Math.round(x)}px, ${Math.round(y - 42)}px, 0) translate(-50%, -100%)`;

            if (lineEl) {
              lineEl.style.display = 'block';
              lineEl.setAttribute('x1', x);
              lineEl.setAttribute('y1', y - 35);
              lineEl.setAttribute('x2', x);
              lineEl.setAttribute('y2', y);
            }
            if (dotEl) {
              dotEl.style.display = 'block';
              dotEl.setAttribute('cx', x);
              dotEl.setAttribute('cy', y);
            }
          } else {
            badgeEl.style.display = 'none';
            if (lineEl) lineEl.style.display = 'none';
            if (dotEl) dotEl.style.display = 'none';
          }
        }
      }
    };
    animate();

    // Responsive Canvas Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const cr = entry.contentRect;
        width = cr.width;
        height = cr.height;
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
      }
    });
    resizeObserver.observe(container);

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
      renderer.dispose();
      if (pointCloudGeometryRef.current) pointCloudGeometryRef.current.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

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
    <div className="relative w-full h-[380px] sm:h-[420px] lg:h-[460px] xl:h-[480px] bg-[#09101f] border border-[#172742] rounded-md overflow-hidden shadow-xl flex flex-col">
      {/* Top Header & Toolbar Bar */}
      <div className="bg-[#09101f]/95 border-b border-[#172742] px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-xs z-20 select-none">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[#00d4ff] shadow-[0_0_8px_#00d4ff]" />
          <span className="font-bold text-white text-xs sm:text-sm">
            2.5D Semantic Elevation Map <span className="text-[#94a3b8] font-normal text-[11px] sm:text-xs">(Top View + Height)</span>
          </span>
        </div>

        {/* Viewport Presets & Controls */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {/* Preset Buttons */}
          <div className="flex bg-[#050913] p-0.5 rounded border border-[#172742]">
            {['Driver', 'Top', 'Side', 'Front'].map((p) => (
              <button
                key={p}
                onClick={() => setCameraPreset(p)}
                className={`px-1.5 sm:px-2 py-0.5 rounded text-[10px] sm:text-[11px] font-semibold transition ${
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
            className={`flex items-center gap-1 px-1.5 sm:px-2 py-1 rounded text-[10px] sm:text-[11px] font-semibold border transition ${
              colorMode === 'semantic'
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 hover:bg-purple-500/30'
                : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 hover:bg-cyan-500/30'
            }`}
          >
            <Eye className="w-3 h-3" />
            <span>{colorMode === 'semantic' ? 'Semantic' : 'Elevation'}</span>
          </button>

          {/* Adaptive Grid Toggle */}
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`px-1.5 sm:px-2 py-1 rounded text-[10px] sm:text-[11px] font-semibold border transition ${
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
            className={`px-1.5 sm:px-2 py-1 rounded text-[10px] sm:text-[11px] font-semibold border transition ${
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
        {/* Dynamic Screen-Space Projected Callouts Overlay with Direct DOM Transforms */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden select-none z-10">
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {TARGET_SPECS.map((s) => (
              <g key={`leader-${s.id}`}>
                <line
                  ref={(el) => (lineRefs.current[s.id] = el)}
                  stroke={s.color}
                  strokeWidth="1.5"
                  strokeDasharray="3 2"
                  style={{ display: 'none' }}
                />
                <circle
                  ref={(el) => (dotRefs.current[s.id] = el)}
                  r="3.5"
                  fill={s.color}
                  style={{ display: 'none' }}
                />
              </g>
            ))}
          </svg>

          {/* Direct DOM Badge Elements */}
          {TARGET_SPECS.map((s) => (
            <div
              key={`badge-${s.id}`}
              ref={(el) => (badgeRefs.current[s.id] = el)}
              className="absolute bg-[#09101f]/95 border rounded px-2 py-0.8 text-[11px] shadow-lg shadow-black/60 pointer-events-none"
              style={{
                display: 'none',
                top: 0,
                left: 0,
                willChange: 'transform',
                borderColor: `${s.color}dd`,
              }}
            >
              <div className="font-bold leading-tight" style={{ color: s.color }}>
                {s.label}
              </div>
              <div className="text-white text-[10px] leading-none mt-0.5">{s.sub}</div>
            </div>
          ))}
        </div>

        {/* Viewport HUD Telemetry: GPU FPS, Provenance, Coordinates */}
        <div className="absolute top-2 left-3 flex flex-wrap items-center gap-1.5 sm:gap-2 pointer-events-none z-10">
          <div className="flex items-center gap-1.5 px-2 py-0.8 rounded bg-[#050913]/90 border border-[#172742] text-[10px] font-mono text-[#38bdf8]">
            <Gauge className="w-3 h-3 text-[#10b981]" />
            <span>WebGL:</span>
            <span ref={fpsTextRef} className="text-white font-bold">60 FPS</span>
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
