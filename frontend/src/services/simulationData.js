/**
 * Deterministic Simulation Engine for 2.5D LiDAR Perception Workstation.
 * Faithfully reproduces the reference autonomous perception scene.
 */

// Simple seeded random number generator
function createRng(seed) {
  let s = seed;
  return function () {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

export function generateSimulationFrame(frameId = '1248') {
  const seed = parseInt(frameId, 10) || 1248;
  const rng = createRng(seed);
  const motion = (seed % 3) * 2.2;

  const points = [];
  const labels = [];
  const confidences = [];

  // 1. Drivable Road (Class 0: Blue, #2563eb)
  // X: -10m to 55m, Y: -4.2m to 4.2m
  const roadCount = 2000;
  for (let i = 0; i < roadCount; i++) {
    const x = -10.0 + rng() * 65.0;
    const y = -4.2 + rng() * 8.4;
    const z = 0.05 - 0.003 * (y * y) + (rng() - 0.5) * 0.03;
    const intensity = 0.2 + rng() * 0.3;
    points.push([x, y, z, intensity]);
    labels.push(0);
    confidences.push(0.96 + rng() * 0.03);
  }

  // 2. Sidewalks (Class 1: Violet, #8b5cf6)
  // Left: Y: -6.2 to -4.2, Right: Y: 4.2 to 6.2
  const sidewalkCount = 600;
  for (let i = 0; i < sidewalkCount; i++) {
    const isLeft = rng() > 0.5;
    const x = -10.0 + rng() * 65.0;
    const y = isLeft ? -6.2 + rng() * 2.0 : 4.2 + rng() * 2.0;
    const z = 0.16 + (rng() - 0.5) * 0.02;
    const intensity = 0.3 + rng() * 0.3;
    points.push([x, y, z, intensity]);
    labels.push(1);
    confidences.push(0.94 + rng() * 0.04);
  }

  // 3. Building / Wall (Class 2: Red, #ef4444)
  // Left barrier wall: Y: -8.8 to -6.2, Height Z up to 3.2m
  const wallCount = 950;
  for (let i = 0; i < wallCount; i++) {
    const x = -8.0 + rng() * 60.0;
    const y = -8.5 + rng() * 2.1;
    const z = 0.2 + rng() * 2.8;
    const intensity = 0.5 + rng() * 0.4;
    points.push([x, y, z, intensity]);
    labels.push(2);
    confidences.push(0.95 + rng() * 0.04);
  }

  // 4. Lush 3D Trees & Vegetation (Class 3: Green, #10b981)
  // Right side trees along sidewalk (Y: 6.5 to 11.0m)
  const treeCenters = [
    [8.0, 7.5],
    [22.0, 8.0],
    [36.0, 8.2],
    [48.0, 7.8],
  ];

  treeCenters.forEach(([tx, ty]) => {
    // Trunk
    for (let i = 0; i < 60; i++) {
      const z = rng() * 2.2;
      const x = tx + (rng() - 0.5) * 0.4;
      const y = ty + (rng() - 0.5) * 0.4;
      points.push([x, y, z, 0.6]);
      labels.push(3);
      confidences.push(0.97);
    }
    // Volumetric Foliage Canopy (Height 2.0 to 5.2m)
    for (let i = 0; i < 280; i++) {
      const radius = 0.5 + rng() * 2.0;
      const theta = rng() * Math.PI * 2;
      const phi = rng() * Math.PI;
      const x = tx + radius * Math.sin(phi) * Math.cos(theta);
      const y = ty + radius * Math.sin(phi) * Math.sin(theta);
      const z = 3.6 + radius * Math.cos(phi) * 0.8;
      points.push([x, y, z, 0.4 + rng() * 0.5]);
      labels.push(3);
      confidences.push(0.93 + rng() * 0.05);
    }
  });

  // 5. Dynamic Vehicles (Class 4: Magenta, #d946ef)
  // Leading car ahead at X = 15.5m, Y = 0.4m
  // Far car ahead at X = 32.0m, Y = -1.5m
  // Oncoming car at X = 25.0m, Y = 2.4m
  const vehicleCenters = [
    [15.5 + motion, 0.4, 0.75, 4.4, 1.8, 1.4],
    [32.0 + motion * 0.7, -1.6, 0.75, 4.2, 1.8, 1.4],
    [25.0 - motion * 0.5, 2.2, 0.75, 4.0, 1.8, 1.4],
  ];

  vehicleCenters.forEach(([vx, vy, vz, len, wid, ht]) => {
    for (let i = 0; i < 240; i++) {
      const x = vx + (rng() - 0.5) * len;
      const y = vy + (rng() - 0.5) * wid;
      const z = vz + (rng() - 0.5) * ht;
      points.push([x, y, z, 0.7 + rng() * 0.3]);
      labels.push(4);
      confidences.push(0.96 + rng() * 0.03);
    }
  });

  // 6. Pedestrians (Class 5: Yellow/Orange, #eab308)
  // Pedestrian on right sidewalk at X = 18.0m, Y = 5.2m
  // Pedestrian on left sidewalk at X = 28.0m, Y = -5.0m
  const pedestrians = [
    [18.0 + motion * 0.35, 5.2],
    [28.0 + motion * 0.2, -5.0],
  ];

  pedestrians.forEach(([px, py]) => {
    for (let i = 0; i < 60; i++) {
      const z = rng() * 1.75;
      const x = px + (rng() - 0.5) * 0.5;
      const y = py + (rng() - 0.5) * 0.5;
      points.push([x, y, z, 0.5]);
      labels.push(5);
      confidences.push(0.94);
    }
  });

  // 7. Street Poles / Signs (Class 6: Cyan, #06b6d4)
  const poles = [
    [5.0, -4.8],
    [20.0, 4.8],
    [35.0, -4.8],
    [50.0, 4.8],
  ];

  poles.forEach(([px, py]) => {
    for (let i = 0; i < 45; i++) {
      const z = rng() * 4.2;
      const x = px + (rng() - 0.5) * 0.2;
      const y = py + (rng() - 0.5) * 0.2;
      points.push([x, y, z, 0.8]);
      labels.push(6);
      confidences.push(0.98);
    }
  });

  // 8. Dynamic Annotations with Leader Lines matching reference image
  const annotations = [
    {
      id: 'wall',
      title: 'Wall (Non-drivable)',
      subtext: 'Height: ~2.5 m',
      color: '#ef4444',
      position: [-6.8, 12.0, 2.5],
    },
    {
      id: 'vehicle',
      title: 'Vehicle (Dynamic)',
      subtext: 'Height: ~1.5 m',
      color: '#d946ef',
      position: [0.4, 15.5, 1.5],
    },
    {
      id: 'tree',
      title: 'Tree (Static)',
      subtext: 'Height: ~5 m',
      color: '#10b981',
      position: [7.8, 22.0, 4.8],
    },
    {
      id: 'pedestrian',
      title: 'Pedestrian (Dynamic)',
      subtext: 'Height: ~1.7 m',
      color: '#eab308',
      position: [5.2, 18.0, 1.7],
    },
    {
      id: 'road',
      title: 'Drivable Road',
      subtext: 'Height: ~0.0 – 0.5 m',
      color: '#38bdf8',
      position: [-0.2, 5.0, 0.1],
    },
  ];

  // 9. Scene Object Counts
  const sceneObjects = {
    Vehicle: 3,
    Pedestrian: 2,
    Motorcycle: 0,
    Bicycle: 1,
    'Static (Pole/Sign)': 4,
    Others: 1,
  };

  const detectedObjects = [
    ...vehicleCenters.map(([x, y, z, length, width, height], index) => ({
      id: `vehicle-${index + 1}`,
      class_id: 4,
      class_name: 'vehicle',
      center: { x, y, z },
      size: { length, width, height },
      distance_m: Math.sqrt(x * x + y * y),
    })),
    ...pedestrians.map(([x, y], index) => ({
      id: `pedestrian-${index + 1}`,
      class_id: 5,
      class_name: 'pedestrian',
      center: { x, y, z: 0.9 },
      size: { length: 0.9, width: 0.7, height: 1.8 },
      distance_m: Math.sqrt(x * x + y * y),
    })),
  ];

  // 10. Performance Telemetry
  const performance = {
    miou_percent: 87.0,
    fps: 18.0,
    latency_ms: 55.0,
    memory_mb: 820.0,
    provenance: 'SIMULATION',
  };

  // 11. System Logs matching reference image
  const systemLogs = [
    { time: '14:32:10', msg: 'Loaded frame 124' },
    { time: '14:32:11', msg: 'Point cloud: 1,284,365 points' },
    { time: '14:32:13', msg: 'Segmentation completed' },
    { time: '14:32:15', msg: 'Adaptive grid generated' },
    { time: '14:32:16', msg: '2.5D map updated' },
    { time: '14:32:17', msg: 'Ready (18 FPS)' },
  ];

  // 12. Continuous 1D Elevation Profile Contour (Distance 0-100m vs Height 0-10m)
  const distance_m = [];
  const height_m = [];
  for (let d = 0; d <= 100; d += 1) {
    distance_m.push(d);
    // Smooth hill and overpass contour matching reference image
    const h = 0.5 + 4.5 * Math.exp(-Math.pow((d - 48) / 16, 2)) + 2.8 * Math.exp(-Math.pow((d - 22) / 8, 2)) + (rng() - 0.5) * 0.15;
    height_m.push(Math.max(0.2, Math.min(8.5, h)));
  }

  // 13. Grid Comparison Metrics (Uniform vs Adaptive)
  const gridComparison = {
    uniform: {
      resolution: 0.05,
      cell_count: 14280,
      occupied_area_m2: 357.0,
      estimated_memory_kb: 456.9,
      point_count: points.length,
    },
    adaptive: {
      base_resolution: 0.5,
      fine_resolution: 0.05,
      cell_count: 4520,
      coarse_cell_count: 1420,
      fine_cell_count: 3100,
      occupied_area_m2: 357.0,
      estimated_memory_kb: 144.6,
      point_count: points.length,
    },
    comparison: {
      cell_count_reduction_percent: -68.3,
      estimated_memory_reduction_percent: -68.3,
      speedup_factor: 3.2,
      points_conserved_percent: 100.0,
    },
  };

  return {
    frame_id: frameId,
    points,
    predicted_labels: labels,
    confidence_scores: confidences,
    total_points: points.length,
    annotations,
    scene_objects: sceneObjects,
    detected_objects: detectedObjects,
    performance,
    system_logs: systemLogs,
    elevation_profile: { distance_m, height_m },
    grid_comparison: gridComparison,
    provenance: 'SIMULATION',
  };
}
