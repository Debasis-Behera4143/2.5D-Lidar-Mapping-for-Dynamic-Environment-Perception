import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { Layers, Cpu, Grid } from 'lucide-react';

export default function SceneOverview({ points = [] }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 180;
    const height = 120;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050913);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(-1.0, -12.0, 9.0);
    camera.lookAt(0, 8, 1);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Build mini point cloud geometry
    const step = Math.max(1, Math.floor(points.length / 800));
    const sampled = points.filter((_, idx) => idx % step === 0);

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(sampled.length * 3);
    const colors = new Float32Array(sampled.length * 3);

    sampled.forEach((pt, i) => {
      positions[i * 3] = pt[1];      // Lateral Y -> Three X
      positions[i * 3 + 1] = pt[2];  // Height Z -> Three Y
      positions[i * 3 + 2] = -pt[0]; // Forward X -> Three -Z

      // Height Turbo-style tint
      const h = Math.max(0, Math.min(1, pt[2] / 4.0));
      colors[i * 3] = 0.1 + h * 0.9;
      colors[i * 3 + 1] = 0.8 - h * 0.4;
      colors[i * 3 + 2] = 1.0 - h * 0.8;
    });

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
    });

    const pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);

    // Continuous slow orbit animation for vivid visualization
    let animationId;
    let angle = 0;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      angle += 0.006;
      camera.position.x = Math.sin(angle) * 3;
      camera.lookAt(0, 10, 1);
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      camera.aspect = w / height;
      camera.updateProjectionMatrix();
      renderer.setSize(w, height);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [points]);

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* 1. Scene Overview Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="flex items-center gap-1.5 text-xs font-bold text-white mb-2">
          <Layers className="w-3.5 h-3.5 text-[#00d4ff]" />
          <span>Scene Overview</span>
        </div>
        <div ref={mountRef} className="w-full h-[120px] rounded bg-[#050913] border border-[#132035] overflow-hidden" />
        <div className="text-[10px] text-[#94a3b8] text-center mt-1.5 font-medium">
          Raw LiDAR Point Cloud (3D)
        </div>
      </div>

      <div className="text-center text-[#38bdf8] text-xs font-bold -my-1">↓</div>

      {/* 2. AI Semantic Segmentation Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="flex items-center gap-1.5 text-xs font-bold text-white mb-2">
          <Cpu className="w-3.5 h-3.5 text-[#3b82f6]" />
          <span>AI Semantic Segmentation</span>
        </div>
        <div className="space-y-1 text-[11px] text-[#cbd5e1]">
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Terrain classification</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Object detection</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Semantic labels</span>
          </div>
        </div>
      </div>

      <div className="text-center text-[#38bdf8] text-xs font-bold -my-1">↓</div>

      {/* 3. Adaptive Grid + 2.5D Mapping Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="flex items-center gap-1.5 text-xs font-bold text-white mb-2">
          <Grid className="w-3.5 h-3.5 text-[#10b981]" />
          <span>Adaptive Grid + 2.5D Mapping</span>
        </div>
        <div className="space-y-1 text-[11px] text-[#cbd5e1]">
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Variable resolution</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Elevation map</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <span>Semantic layers</span>
          </div>
        </div>
      </div>
    </div>
  );
}
