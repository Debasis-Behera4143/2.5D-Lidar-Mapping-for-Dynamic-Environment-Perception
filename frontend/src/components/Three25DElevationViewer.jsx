/**
 * Three25DElevationViewer.jsx
 * High-fidelity 2.5D Elevation Map Viewer.
 * Directly matches Reference Box 11:
 * - Clean coordinate axes: Y (m) (-50 to 50) and X (m) (-50 to 50)
 * - 2.5D Elevation Heatmap with authentic Turbo colormap
 * - Dedicated right-hand vertical colorbar (Height 0.0 to 5.0m)
 * - Optional interactive 3D Relief WebGL mode without visual clutter or congestion
 */

import React, { useEffect, useRef, useState, useMemo } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Turbo colormap approximation for elevation
function getTurboColorRgb(normalizedHeight) {
  const t = Math.max(0, Math.min(1, normalizedHeight));
  if (t < 0.25) {
    const k = t / 0.25;
    return `rgb(${Math.round(25 + k * 20)}, ${Math.round(100 + k * 130)}, 245)`;
  } else if (t < 0.5) {
    const k = (t - 0.25) / 0.25;
    return `rgb(${Math.round(45 + k * 20)}, ${Math.round(230 - k * 30)}, ${Math.round(245 - k * 150)})`;
  } else if (t < 0.75) {
    const k = (t - 0.5) / 0.25;
    return `rgb(${Math.round(65 + k * 170)}, ${Math.round(200 + k * 30)}, ${Math.round(95 - k * 80)})`;
  } else {
    const k = (t - 0.75) / 0.25;
    return `rgb(245, ${Math.round(230 - k * 180)}, ${Math.round(15 - k * 5)})`;
  }
}

export default function Three25DElevationViewer({
  points = [],
  labels = [],
}) {
  const [viewMode, setViewMode] = useState('heatmap'); // 'heatmap' (Reference) | '3dRelief'
  const mountRef = useRef(null);

  // WebGL 3D Relief state
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);

  // Generate 2.5D Elevation Raster Grid from actual LiDAR points (50x50 cells covering -50m to 50m)
  const { elevationGrid } = useMemo(() => {
    const gridSize = 40;
    const grid = Array.from({ length: gridSize }, () => new Float32Array(gridSize).fill(0));

    if (points && points.length > 0) {
      const step = Math.max(1, Math.floor(points.length / 1500));
      for (let i = 0; i < points.length; i += step) {
        const x = points[i][0]; // longitudinal
        const y = points[i][1]; // lateral
        const z = points[i][2]; // height

        // Map (-50..50) into (0..gridSize-1)
        const gx = Math.min(gridSize - 1, Math.max(0, Math.floor(((x + 50) / 100) * gridSize)));
        const gy = Math.min(gridSize - 1, Math.max(0, Math.floor(((y + 50) / 100) * gridSize)));

        // Max height pooling for 2.5D elevation surface
        grid[gy][gx] = Math.max(grid[gy][gx], Math.max(0, z));
      }
    } else {
      // Default reference scene: road intersection at 0.05m, curbs at 0.25m, structures up to 4.5m
      for (let r = 0; r < gridSize; r++) {
        for (let c = 0; c < gridSize; c++) {
          const isRoadX = Math.abs(r - gridSize / 2) < 4;
          const isRoadY = Math.abs(c - gridSize / 2) < 4;
          if (isRoadX || isRoadY) {
            grid[r][c] = 0.08;
          } else if (Math.abs(r - gridSize / 2) < 6 || Math.abs(c - gridSize / 2) < 6) {
            grid[r][c] = 0.28; // sidewalk
          } else {
            // Surrounding urban buildings and trees
            const d = Math.sqrt(Math.pow(r - gridSize / 2, 2) + Math.pow(c - gridSize / 2, 2));
            grid[r][c] = d > 12 ? Math.min(4.8, 1.2 + (Math.sin(r * 0.8) + Math.cos(c * 0.8)) * 1.5) : 0.4;
          }
        }
      }
    }

    return { elevationGrid: grid };
  }, [points]);

  // WebGL Setup for 3D Relief mode
  useEffect(() => {
    if (viewMode !== '3dRelief') return;
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 300;
    const height = container.clientHeight || 150;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x040814);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 200);
    camera.position.set(-18.0, 16.0, -20.0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 1.2, 0);
    controlsRef.current = controls;

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambient);
    const dir = new THREE.DirectionalLight(0x00d4ff, 0.8);
    dir.position.set(15, 25, -15);
    scene.add(dir);

    // Ground Grid
    const grid = new THREE.GridHelper(24, 24, 0x00d4ff, 0x14233c);
    scene.add(grid);

    // Build 2.5D Instanced Elevation Pillars
    const numPillars = elevationGrid.length * elevationGrid[0].length;
    const boxGeo = new THREE.BoxGeometry(0.5, 1, 0.5);
    const boxMat = new THREE.MeshStandardMaterial({ roughness: 0.3, metalness: 0.2 });
    const mesh = new THREE.InstancedMesh(boxGeo, boxMat, numPillars);

    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    let idx = 0;
    const size = elevationGrid.length;

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const h = Math.max(0.08, elevationGrid[r][c]);
        const px = (c - size / 2) * 0.55;
        const pz = (r - size / 2) * 0.55;
        const py = h / 2;

        dummy.position.set(px, py, pz);
        dummy.scale.set(1, h, 1);
        dummy.updateMatrix();
        mesh.setMatrixAt(idx, dummy.matrix);

        // Turbo color
        const normH = Math.min(1.0, h / 5.0);
        if (normH < 0.25) {
          color.setRGB(0.1 + normH * 0.4, 0.4 + normH * 2.0, 0.95);
        } else if (normH < 0.5) {
          const k = (normH - 0.25) / 0.25;
          color.setRGB(0.1 + k * 0.1, 0.9 - k * 0.1, 0.95 - k * 0.6);
        } else if (normH < 0.75) {
          const k = (normH - 0.5) / 0.25;
          color.setRGB(0.2 + k * 0.75, 0.8 + k * 0.15, 0.35 - k * 0.3);
        } else {
          const k = (normH - 0.75) / 0.25;
          color.setRGB(0.95, 0.95 - k * 0.7, 0.05);
        }
        mesh.setColorAt(idx, color);
        idx++;
      }
    }
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    scene.add(mesh);

    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      boxGeo.dispose();
      boxMat.dispose();
      if (container) container.innerHTML = '';
    };
  }, [viewMode, elevationGrid]);

  return (
    <div className="w-full h-full flex flex-col select-none text-xs">
      {/* Top Header Mode Switcher (Clean, non-intrusive) */}
      <div className="flex items-center justify-between pb-1.5 mb-1 border-b border-[#14233c]">
        <span className="text-[11px] font-bold text-white tracking-tight">
          {viewMode === 'heatmap' ? '2.5D Elevation Map (Top View)' : '3D Elevation Surface Relief'}
        </span>

        {/* Mode Toggle Button */}
        <div className="flex items-center gap-1 bg-[#050b18] p-0.5 rounded border border-[#1a3258] text-[9.5px]">
          <button
            onClick={() => setViewMode('heatmap')}
            className={`px-2 py-0.5 rounded font-medium transition cursor-pointer ${
              viewMode === 'heatmap'
                ? 'bg-blue-600 text-white font-bold'
                : 'text-[#718eb3] hover:text-white'
            }`}
          >
            Heatmap (2D)
          </button>
          <button
            onClick={() => setViewMode('3dRelief')}
            className={`px-2 py-0.5 rounded font-medium transition cursor-pointer ${
              viewMode === '3dRelief'
                ? 'bg-blue-600 text-white font-bold'
                : 'text-[#718eb3] hover:text-white'
            }`}
          >
            3D Relief
          </button>
        </div>
      </div>

      {/* Main Map + Colorbar Row */}
      <div className="flex-1 flex flex-row items-center gap-2 min-h-0">
        {/* Left Side: 2D Heatmap or 3D WebGL Canvas */}
        <div className="flex-1 h-full relative flex items-center justify-center min-w-0">
          {viewMode === 'heatmap' ? (
            /* Clean Authentic 2.5D Elevation Heatmap with Coordinate Ticks */
            <div className="w-full h-full relative flex flex-col justify-between py-0.5">
              {/* Top Y-Axis Label */}
              <div className="flex justify-between items-center text-[8.5px] font-mono text-[#718eb3] px-5">
                <span>Y: +50m</span>
                <span className="text-[8px] text-[#52719c]">Crossroad Elevation Corridor</span>
              </div>

              {/* Center Map Raster with Side Ticks */}
              <div className="flex-1 flex items-center gap-1 px-1 my-0.5">
                <span className="text-[8px] font-mono text-[#718eb3] w-4 text-right">0</span>
                <div className="flex-1 h-full bg-[#030712] border border-[#14233c] rounded relative overflow-hidden flex items-center justify-center p-0.5">
                  <svg viewBox="0 0 40 40" className="w-full h-full" preserveAspectRatio="none">
                    {elevationGrid.map((row, rIdx) =>
                      Array.from(row).map((val, cIdx) => {
                        const normH = Math.min(1.0, val / 5.0);
                        const fillColor = getTurboColorRgb(normH);
                        return (
                          <rect
                            key={`${rIdx}-${cIdx}`}
                            x={cIdx}
                            y={rIdx}
                            width="1"
                            height="1"
                            fill={fillColor}
                          />
                        );
                      })
                    )}
                  </svg>
                </div>
              </div>

              {/* Bottom X-Axis Ticks & Label */}
              <div className="flex justify-between items-center text-[8.5px] font-mono text-[#718eb3] px-5">
                <span>-50m</span>
                <span>X (m): 0</span>
                <span>+50m</span>
              </div>
            </div>
          ) : (
            /* 3D WebGL Relief Container */
            <div ref={mountRef} className="w-full h-full rounded overflow-hidden cursor-grab active:cursor-grabbing border border-[#14233c]" />
          )}
        </div>

        {/* Right Side: Dedicated Vertical Colorbar (Height 0.0 to 5.0m) */}
        <div className="w-12 shrink-0 h-full flex flex-col items-center justify-between py-1 bg-[#050b18] border border-[#14233c] rounded px-1 text-[8.5px] font-mono">
          <span className="text-[7.5px] text-[#718eb3] font-sans font-bold leading-tight text-center">
            Height<br />(m)
          </span>

          <span className="text-red-400 font-bold">5.0</span>

          {/* Smooth Turbo Gradient Bar */}
          <div
            className="w-2.5 flex-1 my-1 rounded-sm shadow-inner"
            style={{
              background: 'linear-gradient(to bottom, rgb(245, 50, 10), rgb(235, 230, 20), rgb(65, 200, 95), rgb(45, 230, 245), rgb(25, 100, 245))',
            }}
          />

          <span className="text-yellow-400 font-bold">2.5</span>

          {/* Lower Gradient */}
          <div
            className="w-2.5 flex-1 my-1 rounded-sm shadow-inner"
            style={{
              background: 'linear-gradient(to bottom, rgb(235, 230, 20), rgb(65, 200, 95), rgb(45, 230, 245), rgb(25, 100, 245))',
            }}
          />

          <span className="text-blue-400 font-bold">0.0</span>
        </div>
      </div>
    </div>
  );
}
