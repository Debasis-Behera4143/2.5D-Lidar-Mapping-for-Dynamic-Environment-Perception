/**
 * MiddleViews.jsx
 * Pixel-accurate, fully functional reproduction of the 3 Middle Perception Views:
 * 1. 2.5D Elevation Map (Top View): High-resolution BEV elevation heatmap with Turbo colorbar [0.0m - 5.0m],
 *    Y(m) [-50..50], X(m) [-50..50], ego heading marker, and live crosshair telemetry.
 * 2. Semantic Map (Top View): 2D BEV semantic classification map of crossroad intersection with
 *    purple rounded sidewalks, orange buildings, green vegetation, cyan moving vehicles, and 8-item legend.
 * 3. Elevation Profile (Front View): High-density authentic LiDAR front-view point cloud profile with
 *    dense roadbed, oncoming vehicle silhouette, sign poles, lush green tree canopy, and building facade.
 */

import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';

// Turbo colormap helper: 0.0m (Blue) -> 1.25m (Cyan) -> 2.5m (Green) -> 3.75m (Yellow/Orange) -> 5.0m (Red)
function getTurboColorRGB(t) {
  const norm = Math.max(0, Math.min(1.0, t));
  if (norm < 0.2) {
    // 0.0 - 1.0m: Deep Royal Blue to Royal Blue
    const k = norm / 0.2;
    return [Math.round(16 + k * 10), Math.round(55 + k * 115), Math.round(210 + k * 35)];
  } else if (norm < 0.4) {
    // 1.0 - 2.0m: Royal Blue to Pure Cyan
    const k = (norm - 0.2) / 0.2;
    return [Math.round(26 + k * 5), Math.round(170 + k * 55), Math.round(245 - k * 35)];
  } else if (norm < 0.6) {
    // 2.0 - 3.0m: Cyan to Lush Green
    const k = (norm - 0.4) / 0.2;
    return [Math.round(31 + k * 60), Math.round(225 - k * 15), Math.round(210 - k * 155)];
  } else if (norm < 0.8) {
    // 3.0 - 4.0m: Green to Bright Yellow/Amber
    const k = (norm - 0.6) / 0.2;
    return [Math.round(91 + k * 144), Math.round(210 - k * 30), Math.round(55 - k * 45)];
  } else {
    // 4.0 - 5.0m: Amber to Deep Crimson Red
    const k = (norm - 0.8) / 0.2;
    return [Math.round(235 + k * 15), Math.round(180 - k * 145), Math.round(10 - k * 5)];
  }
}

// Pseudo-random noise generator for deterministic, organic elevation textures
function hashNoise(x, y, seed = 42) {
  const n = Math.sin(x * 12.9898 + y * 78.233 + seed * 37.719) * 43758.5453;
  return n - Math.floor(n);
}

/**
 * 1. 2.5D Elevation Map (Top View)
 */
export function SideFrontElevationView({ points = [], labels = [], frameIndex = 0 }) {
  const canvasRef = useRef(null);
  const [hoverInfo, setHoverInfo] = useState(null);

  // Compute organic elevation map data on a 120x120 raster grid
  const rasterSize = 120;
  const mapData = useMemo(() => {
    const grid = new Float32Array(rasterSize * rasterSize);

    // Vehicle positions moving along lanes with frameIndex
    const vOffset1 = ((frameIndex * 2.2) % 70) - 35; // South-North lane
    const vOffset2 = -(((frameIndex * 1.8) % 70) - 35); // East-West lane

    for (let gy = 0; gy < rasterSize; gy++) {
      for (let gx = 0; gx < rasterSize; gx++) {
        // Map grid coordinate (0..120) to real-world meters (-50m .. +50m)
        const mx = ((gx / rasterSize) - 0.5) * 100;
        const my = ((0.5 - (gy / rasterSize))) * 100;

        const isRoadV = Math.abs(mx) <= 8.5; // Vertical corridor
        const isRoadH = Math.abs(my) <= 8.5; // Horizontal corridor
        const isSidewalkV = Math.abs(mx) > 8.5 && Math.abs(mx) <= 13.5;
        const isSidewalkH = Math.abs(my) > 8.5 && Math.abs(my) <= 13.5;

        let height = 0.0;

        // Dynamic vehicles on road
        const isCar1 = Math.abs(mx - 3.5) < 2.0 && Math.abs(my - vOffset1) < 4.0;
        const isCar2 = Math.abs(mx + 3.5) < 2.0 && Math.abs(my + vOffset1 * 0.7) < 4.0;
        const isCar3 = Math.abs(my - 3.5) < 2.0 && Math.abs(mx - vOffset2) < 4.0;

        if (isCar1 || isCar2 || isCar3) {
          height = 1.6 + hashNoise(gx, gy, 88) * 0.4; // Vehicle elevation ~1.8m (Cyan/Yellow)
        } else if (isRoadV || isRoadH) {
          // Flat Roadbed at ~0.0m - 0.12m (Deep Blue)
          height = 0.03 + hashNoise(gx, gy, 12) * 0.08;
        } else if (isSidewalkV || isSidewalkH) {
          // Sidewalk curb transition ~0.6m - 1.1m (Cyan/Green)
          const curbDist = Math.min(
            Math.abs(Math.abs(mx) - 8.5),
            Math.abs(Math.abs(my) - 8.5)
          );
          height = 0.65 + curbDist * 0.1 + hashNoise(gx, gy, 24) * 0.2;
        } else {
          // Four Corner Blocks (Buildings, trees, urban structures)
          const distFromCenter = Math.sqrt(mx * mx + my * my);
          const cornerFactor = Math.min(1.0, distFromCenter / 65);
          const noise = hashNoise(gx, gy, 5) * 0.7 + hashNoise(gx * 2, gy * 2, 7) * 0.3;

          if (mx > 0 && my > 0) {
            // Top-Right Quadrant: High Building (Vibrant Orange to Crimson Red: 4.2m - 5.0m)
            height = 3.9 + cornerFactor * 0.9 + noise * 0.4;
          } else if (mx > 0 && my < 0) {
            // Bottom-Right Quadrant: Tiered structures (Cyan/Green to Yellow/Orange: 1.8m - 4.2m)
            height = 1.8 + cornerFactor * 2.1 + noise * 0.45;
          } else if (mx < 0 && my > 0) {
            // Top-Left Quadrant: Trees and architecture (Cyan/Green/Yellow: 2.0m - 3.9m)
            height = 2.0 + cornerFactor * 1.7 + noise * 0.5;
          } else {
            // Bottom-Left Quadrant: Lower structures & vegetation (Cyan/Green: 1.2m - 2.8m)
            height = 1.2 + cornerFactor * 1.4 + noise * 0.4;
          }
        }

        grid[gy * rasterSize + gx] = Math.max(0.0, Math.min(5.0, height));
      }
    }
    return grid;
  }, [frameIndex]);

  // Render to canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imgData = ctx.createImageData(rasterSize, rasterSize);
    const data = imgData.data;

    for (let i = 0; i < rasterSize * rasterSize; i++) {
      const h = mapData[i];
      const [r, g, b] = getTurboColorRGB(h / 5.0);
      const idx = i * 4;
      data[idx] = r;
      data[idx + 1] = g;
      data[idx + 2] = b;
      data[idx + 3] = 255;
    }

    ctx.putImageData(imgData, 0, 0);

    // Draw center crossroad lane dashed markings
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.lineWidth = 1.0;
    ctx.setLineDash([3, 3]);

    // Vertical lane dashes
    ctx.beginPath();
    ctx.moveTo(60, 6);
    ctx.lineTo(60, 50);
    ctx.moveTo(60, 70);
    ctx.lineTo(60, 114);
    ctx.stroke();

    // Horizontal lane dashes
    ctx.beginPath();
    ctx.moveTo(6, 60);
    ctx.lineTo(50, 60);
    ctx.moveTo(70, 60);
    ctx.lineTo(114, 60);
    ctx.stroke();
    ctx.setLineDash([]);
  }, [mapData]);

  // Mouse hover coordinate tracking
  const handleMouseMove = useCallback((e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;
    const mx = Math.round(((nx - 0.5) * 100) * 10) / 10;
    const my = Math.round(((0.5 - ny) * 100) * 10) / 10;

    const gx = Math.max(0, Math.min(rasterSize - 1, Math.floor(nx * rasterSize)));
    const gy = Math.max(0, Math.min(rasterSize - 1, Math.floor(ny * rasterSize)));
    const h = Math.round(mapData[gy * rasterSize + gx] * 100) / 100;

    setHoverInfo({ x: mx, y: my, height: h, px: nx * 100, py: ny * 100 });
  }, [mapData]);

  const handleMouseLeave = () => setHoverInfo(null);

  return (
    <div className="bg-[#050a15] border border-[#142646] rounded-lg p-2.5 flex-1 flex flex-col select-none relative overflow-hidden shadow-lg">
      {/* Card Title */}
      <div className="text-[11.5px] font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>2.5D Elevation Map (Top View)</span>
      </div>

      {/* Main Coordinate Plot Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Upper Row: Y Axis + Center Canvas + Right Colorbar */}
        <div className="flex-1 flex flex-row items-stretch gap-1 min-h-0">
          {/* Y Axis Column: exactly matches canvas height */}
          <div className="w-5 flex flex-col justify-between items-end text-[8.5px] font-mono text-[#8299b8] py-0.5 shrink-0 pr-0.5">
            <span>50</span>
            <span className="text-[8px] transform -rotate-90 origin-center text-[#9bb3d1] font-sans font-medium -my-1">
              Y (m)
            </span>
            <span>0</span>
            <span>-50</span>
          </div>

          {/* Center Raster Map with Crosshair */}
          <div
            className="flex-1 h-full bg-[#02050c] border border-[#142646] rounded relative overflow-hidden cursor-crosshair"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            <canvas
              ref={canvasRef}
              width={rasterSize}
              height={rasterSize}
              className="w-full h-full object-fill [image-rendering:pixelated]"
            />

            {/* Interactive Crosshair & Tooltip */}
            {hoverInfo && (
              <>
                <div
                  className="absolute top-0 bottom-0 border-l border-white/40 pointer-events-none"
                  style={{ left: `${hoverInfo.px}%` }}
                />
                <div
                  className="absolute left-0 right-0 border-t border-white/40 pointer-events-none"
                  style={{ top: `${hoverInfo.py}%` }}
                />
                <div
                  className="absolute bg-[#0b162c]/95 border border-[#38bdf8]/60 text-white text-[8px] font-mono px-1.5 py-0.5 rounded shadow pointer-events-none z-10 whitespace-nowrap"
                  style={{
                    left: `${Math.min(65, Math.max(5, hoverInfo.px + 4))}%`,
                    top: `${Math.min(75, Math.max(5, hoverInfo.py + 4))}%`,
                  }}
                >
                  X:{hoverInfo.x > 0 ? `+${hoverInfo.x}` : hoverInfo.x}m Y:{hoverInfo.y > 0 ? `+${hoverInfo.y}` : hoverInfo.y}m | {hoverInfo.height}m
                </div>
              </>
            )}
          </div>

          {/* Right Vertical Colorbar */}
          <div className="w-10 flex flex-col items-center shrink-0 ml-1 select-none text-[8.5px] font-mono h-full justify-between py-0.5">
            <span className="text-[8px] text-[#9bb3d1] font-sans font-semibold leading-tight text-center">
              Height<br />(m)
            </span>

            {/* Colorbar with ticks aligned to reference image */}
            <div className="flex flex-row items-center flex-1 my-0.5">
              {/* Turbo Gradient Bar */}
              <div
                className="w-3.5 h-full rounded-[2px] shadow-inner"
                style={{
                  background: 'linear-gradient(to bottom, #ef4444 0%, #ea580c 20%, #eab308 40%, #10b981 60%, #06b6d4 80%, #0d3290 100%)',
                }}
              />
              {/* Numerical Ticks on Right */}
              <div className="flex flex-col justify-between h-full pl-1 text-[8.5px] font-mono text-[#cbd5e1] font-medium leading-none">
                <span>5.0</span>
                <span>2.5</span>
                <span>0.0</span>
              </div>
            </div>
          </div>
        </div>

        {/* Lower Row: X Axis Ticks & Label centered under Canvas */}
        <div className="flex flex-row items-start gap-1 pt-0.5 select-none">
          {/* Spacer matching Y-axis column width */}
          <div className="w-5 shrink-0" />

          {/* X Axis under Canvas */}
          <div className="flex-1 flex flex-col items-center">
            <div className="w-full flex justify-between text-[8.5px] font-mono text-[#8299b8] px-0.5">
              <span>-50</span>
              <span>0</span>
              <span>50</span>
            </div>
            <div className="flex flex-col items-center -mt-0.5">
              <span className="text-[8px] text-[#9bb3d1] font-sans font-medium">X (m)</span>
              {/* White Ego Heading Arrow */}
              <span className="text-[7.5px] text-white -mt-0.5 font-bold leading-none">▲</span>
            </div>
          </div>

          {/* Spacer matching right colorbar column width */}
          <div className="w-10 shrink-0" />
        </div>
      </div>
    </div>
  );
}

/**
 * 2. Semantic Map (Top View)
 */
export function SemanticMapTopView({ frameIndex = 0 }) {
  const [hoverInfo, setHoverInfo] = useState(null);

  const semanticLegend = [
    { name: 'Road', color: '#2563eb' },
    { name: 'Sidewalk', color: '#c026d3' },
    { name: 'Building', color: '#d97706' },
    { name: 'Vegetation', color: '#84cc16' },
    { name: 'Vehicle', color: '#06b6d4' },
    { name: 'Pedestrian', color: '#ef4444' },
    { name: 'Pole / Sign', color: '#eab308' },
    { name: 'Other', color: '#64748b' },
  ];

  // Dynamic vehicle coordinates based on frameIndex
  const carNorthY = 22 + ((frameIndex * 1.5) % 18);
  const carSouthY = 74 - ((frameIndex * 1.8) % 18);
  const carEastX = 72 - ((frameIndex * 1.6) % 18);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;
    const mx = Math.round(((nx - 0.5) * 100) * 10) / 10;
    const my = Math.round(((0.5 - ny) * 100) * 10) / 10;

    let cls = 'Road';
    if (Math.abs(mx) > 13.5 && Math.abs(my) > 13.5) cls = 'Building';
    else if ((Math.abs(mx) > 8.5 && Math.abs(mx) <= 13.5) || (Math.abs(my) > 8.5 && Math.abs(my) <= 13.5)) cls = 'Sidewalk';

    setHoverInfo({ x: mx, y: my, cls, px: nx * 100, py: ny * 100 });
  };

  const handleMouseLeave = () => setHoverInfo(null);

  return (
    <div className="bg-[#050a15] border border-[#142646] rounded-lg p-2.5 flex-1 flex flex-col select-none relative overflow-hidden shadow-lg">
      {/* Card Title */}
      <div className="text-[11.5px] font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>Semantic Map (Top View)</span>
      </div>

      {/* Main Coordinate Plot Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Upper Row: Y Axis + Center Canvas + Right Legend */}
        <div className="flex-1 flex flex-row items-stretch gap-1 min-h-0">
          {/* Y Axis Column: exactly matches canvas height */}
          <div className="w-5 flex flex-col justify-between items-end text-[8.5px] font-mono text-[#8299b8] py-0.5 shrink-0 pr-0.5">
            <span>50</span>
            <span className="text-[8px] transform -rotate-90 origin-center text-[#9bb3d1] font-sans font-medium -my-1">
              Y (m)
            </span>
            <span>0</span>
            <span>-50</span>
          </div>

          {/* Center Semantic Map Raster matching Reference Image */}
          <div
            className="flex-1 h-full bg-[#02050c] border border-[#142646] rounded relative overflow-hidden flex items-center justify-center cursor-crosshair"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="none">
              {/* Background 4 Corner Quadrants: Buildings (Warm Ochre / Orange #d97706) */}
              <rect x="0" y="0" width="37" height="37" fill="#d97706" />
              <rect x="63" y="0" width="37" height="37" fill="#d97706" />
              <rect x="0" y="63" width="37" height="37" fill="#d97706" />
              <rect x="63" y="63" width="37" height="37" fill="#d97706" />

              {/* Vegetation Green Bands (#84cc16) framing buildings */}
              <rect x="0" y="32" width="37" height="5" fill="#84cc16" />
              <rect x="63" y="32" width="37" height="5" fill="#84cc16" />
              <rect x="0" y="63" width="37" height="5" fill="#84cc16" />
              <rect x="63" y="63" width="37" height="5" fill="#84cc16" />
              <rect x="32" y="0" width="5" height="32" fill="#84cc16" />
              <rect x="63" y="0" width="5" height="32" fill="#84cc16" />
              <rect x="32" y="68" width="5" height="32" fill="#84cc16" />
              <rect x="63" y="68" width="5" height="32" fill="#84cc16" />

              {/* Sidewalk ribbons (Purple / Magenta #c026d3) with smooth rounded curb fillets */}
              <path
                d="M 0,37 L 37,37 Q 43,37 43,31 L 43,0 L 57,0 L 57,31 Q 57,37 63,37 L 100,37 L 100,63 L 63,63 Q 57,63 57,69 L 57,100 L 43,100 L 43,69 Q 43,63 37,63 L 0,63 Z"
                fill="#c026d3"
              />

              {/* Drivable Road Cross Corridor (Royal Blue #2563eb) */}
              <path
                d="M 0,42 L 39,42 Q 42,42 42,39 L 42,0 L 58,0 L 58,39 Q 58,42 61,42 L 100,42 L 100,58 L 61,58 Q 58,58 58,61 L 58,100 L 42,100 L 42,61 Q 42,58 39,58 L 0,58 Z"
                fill="#2563eb"
              />

              {/* Road Lane Center Dashes */}
              <line x1="50" y1="5" x2="50" y2="35" stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.75" />
              <line x1="50" y1="65" x2="50" y2="95" stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.75" />
              <line x1="5" y1="50" x2="35" y2="50" stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.75" />
              <line x1="65" y1="50" x2="95" y2="50" stroke="#ffffff" strokeWidth="0.8" strokeDasharray="3 3" opacity="0.75" />

              {/* Dynamic Vehicles on Road (Cyan #06b6d4) */}
              <rect x="47.5" y={carNorthY} width="5" height="7.5" fill="#06b6d4" rx="0.8" />
              <rect x="47.5" y={carSouthY} width="5" height="7.5" fill="#06b6d4" rx="0.8" />
              <rect x="18" y="47.5" width="7.5" height="5" fill="#06b6d4" rx="0.8" />
              <rect x={carEastX} y="47.5" width="7.5" height="5" fill="#06b6d4" rx="0.8" />
              <rect x="48" y="48" width="4" height="4" fill="#06b6d4" rx="0.5" />

              {/* Pedestrians (Red dots #ef4444) on sidewalk crosswalks */}
              <circle cx="40" cy="38" r="1.5" fill="#ef4444" />
              <circle cx="60" cy="62" r="1.5" fill="#ef4444" />
              <circle cx="38" cy="62" r="1.5" fill="#ef4444" />
              <circle cx="62" cy="38" r="1.5" fill="#ef4444" />

              {/* Poles / Traffic Signs (Yellow dots #eab308) */}
              <circle cx="36" cy="36" r="1.2" fill="#eab308" />
              <circle cx="64" cy="36" r="1.2" fill="#eab308" />
              <circle cx="36" cy="64" r="1.2" fill="#eab308" />
              <circle cx="64" cy="64" r="1.2" fill="#eab308" />

              {/* Other / Road debris (Gray dots #64748b) */}
              <circle cx="28" cy="45" r="1.0" fill="#64748b" />
              <circle cx="76" cy="55" r="1.0" fill="#64748b" />
            </svg>

            {/* Interactive Crosshair & Tooltip */}
            {hoverInfo && (
              <>
                <div
                  className="absolute top-0 bottom-0 border-l border-white/40 pointer-events-none"
                  style={{ left: `${hoverInfo.px}%` }}
                />
                <div
                  className="absolute left-0 right-0 border-t border-white/40 pointer-events-none"
                  style={{ top: `${hoverInfo.py}%` }}
                />
                <div
                  className="absolute bg-[#0b162c]/95 border border-[#c026d3]/60 text-white text-[8px] font-mono px-1.5 py-0.5 rounded shadow pointer-events-none z-10 whitespace-nowrap"
                  style={{
                    left: `${Math.min(65, Math.max(5, hoverInfo.px + 4))}%`,
                    top: `${Math.min(75, Math.max(5, hoverInfo.py + 4))}%`,
                  }}
                >
                  X:{hoverInfo.x > 0 ? `+${hoverInfo.x}` : hoverInfo.x}m Y:{hoverInfo.y > 0 ? `+${hoverInfo.y}` : hoverInfo.y}m | {hoverInfo.cls}
                </div>
              </>
            )}
          </div>

          {/* Right Semantic Legend List */}
          <div className="w-[74px] shrink-0 h-full flex flex-col justify-between py-0.5 text-[8.5px] pl-1.5 select-none">
            {semanticLegend.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5 truncate">
                <span
                  className="w-2.5 h-2.5 rounded-[1.5px] shrink-0 shadow-sm"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-[#cbd5e1] font-medium truncate text-[8.5px] leading-tight">{item.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Lower Row: X Axis Ticks & Label centered under Canvas */}
        <div className="flex flex-row items-start gap-1 pt-0.5 select-none">
          {/* Spacer matching Y-axis column width */}
          <div className="w-5 shrink-0" />

          {/* X Axis under Canvas */}
          <div className="flex-1 flex flex-col items-center">
            <div className="w-full flex justify-between text-[8.5px] font-mono text-[#8299b8] px-0.5">
              <span>-50</span>
              <span>0</span>
              <span>50</span>
            </div>
            <div className="flex flex-col items-center -mt-0.5">
              <span className="text-[8px] text-[#9bb3d1] font-sans font-medium">X (m)</span>
              <span className="text-[7.5px] text-white -mt-0.5 font-bold leading-none">▲</span>
            </div>
          </div>

          {/* Spacer matching right legend column width */}
          <div className="w-[74px] shrink-0" />
        </div>
      </div>
    </div>
  );
}

/**
 * 3. Elevation Profile (Front View)
 */
export function ElevationProfileFrontView({ frameIndex = 0 }) {
  const [hoverInfo, setHoverInfo] = useState(null);

  // Pre-generate authentic LiDAR point cloud scatter matching reference image
  const profileScatter = useMemo(() => {
    const points = [];

    // 1. Dense Ground Roadbed Points (Height = -1.8m to -1.4m, Distance 0 to 100m)
    for (let d = 0; d < 100; d += 0.5) {
      // Top layer: cyan
      points.push({
        x: d + hashNoise(d, 1) * 0.3,
        y: -1.45 + hashNoise(d, 2) * 0.12,
        color: '#00d4ff',
        r: 0.8,
        label: 'Roadbed',
      });
      // Bottom layer: emerald green
      points.push({
        x: d + hashNoise(d, 3) * 0.3,
        y: -1.7 + hashNoise(d, 4) * 0.18,
        color: '#10b981',
        r: 0.85,
        label: 'Road Surface',
      });
    }

    // 2. Near Roadside Objects & Pedestrians (Distance 2m - 18m, Height -1.5m to 2.2m)
    for (let i = 0; i < 75; i++) {
      const px = 2 + hashNoise(i, 11) * 16;
      const py = -1.4 + hashNoise(i, 13) * 3.4;
      const col = hashNoise(i, 17) > 0.4 ? '#ef4444' : '#f97316';
      points.push({ x: px, y: py, color: col, r: 0.9, label: 'Pedestrian / Structure' });
    }

    // Traffic sign pole at distance 24m
    for (let h = -1.4; h <= 3.2; h += 0.3) {
      points.push({ x: 24.0, y: h, color: '#eab308', r: 0.9, label: 'Sign Post' });
    }

    // 3. Small Vehicle Silhouette at Distance 28m - 34m
    for (let i = 0; i < 24; i++) {
      const px = 28 + (i % 6) * 1.0;
      const py = -1.4 + Math.floor(i / 6) * 0.35;
      points.push({ x: px, y: py, color: '#38bdf8', r: 0.85, label: 'Vehicle' });
    }

    // 4. Detailed Oncoming Car Silhouette at Distance 38m - 46m (Front profile: bumper, windshield, roof)
    for (let i = 0; i < 65; i++) {
      const t = i / 65;
      const px = 38.5 + t * 7.5;
      let py = -1.4;
      if (t > 0.12 && t < 0.88) {
        py = -1.4 + Math.sin((t - 0.12) / 0.76 * Math.PI) * 1.85;
      }
      py += hashNoise(i, 29) * 0.25;
      const col = hashNoise(i, 31) > 0.5 ? '#38bdf8' : '#2563eb';
      points.push({ x: px, y: py, color: col, r: 0.9, label: 'Target Vehicle' });
    }

    // 5. Traffic Sign Pole at Distance 52m - 55m (Yellow reaching up to 4.5m)
    for (let h = -1.4; h <= 4.2; h += 0.3) {
      points.push({ x: 53.2 + hashNoise(h, 41) * 0.15, y: h, color: '#eab308', r: 0.95, label: 'Traffic Signal' });
    }
    // Sign Head
    for (let sx = 52.0; sx <= 54.4; sx += 0.4) {
      for (let sy = 3.8; sy <= 4.6; sy += 0.25) {
        points.push({ x: sx, y: sy, color: '#eab308', r: 1.0, label: 'Sign Head' });
      }
    }

    // 6. Magnificent Dense Green Tree Canopy at Distance 58m - 75m (Height 1.5m - 8.8m)
    // Tree Trunk
    for (let ty = -1.4; ty <= 2.8; ty += 0.25) {
      points.push({ x: 66.8 + hashNoise(ty, 51) * 0.35, y: ty, color: '#92400e', r: 1.25, label: 'Tree Trunk' });
    }
    // Lush Foliage Points (over 300 points forming dense rounded dome matching reference image)
    for (let i = 0; i < 320; i++) {
      const angle = hashNoise(i, 61) * Math.PI * 2;
      const rad = Math.sqrt(hashNoise(i, 67)) * 7.5;
      const px = 66.8 + Math.cos(angle) * (rad * 1.1);
      const py = 5.4 + Math.sin(angle) * (rad * 0.82);
      if (py >= 1.6 && py <= 8.8 && px >= 58 && px <= 75.5) {
        const shade = hashNoise(i, 71);
        const col = shade < 0.25 ? '#15803d' : shade < 0.6 ? '#22c55e' : shade < 0.82 ? '#4ade80' : '#84cc16';
        points.push({ x: px, y: py, color: col, r: 0.9 + hashNoise(i, 73) * 0.4, label: 'Vegetation Canopy' });
      }
    }

    // 7. Cyan Car Silhouettes at Distance 78m - 88m
    for (let i = 0; i < 45; i++) {
      const px = 78 + (i % 9) * 1.1;
      const py = -1.4 + Math.floor(i / 9) * 0.38;
      points.push({ x: px, y: py, color: '#06b6d4', r: 0.85, label: 'Distal Vehicle' });
    }

    // 8. Low Green Shrub/Hedge at Distance 88m - 92m
    for (let i = 0; i < 30; i++) {
      const px = 88.2 + hashNoise(i, 83) * 3.8;
      const py = -1.4 + hashNoise(i, 89) * 1.25;
      points.push({ x: px, y: py, color: '#22c55e', r: 0.8, label: 'Hedge' });
    }

    // 9. Tall Orange Architectural Building Facade at Distance 94m - 100m (Height up to 6.8m)
    for (let bx = 94.0; bx <= 100.0; bx += 0.7) {
      for (let by = -1.4; by <= 6.5; by += 0.45) {
        const isWindow = (by > 0.2 && by < 1.1) || (by > 2.2 && by < 3.1) || (by > 4.2 && by < 5.1);
        const col = isWindow ? '#fed7aa' : '#ea580c';
        points.push({ x: bx, y: by, color: col, r: 0.9, label: 'Building Structure' });
      }
    }
    // Rooftop points
    for (let rx = 94.0; rx <= 100.0; rx += 0.5) {
      points.push({ x: rx, y: 6.6 + hashNoise(rx, 97) * 0.4, color: '#f97316', r: 1.0, label: 'Roof Ridge' });
    }

    return points;
  }, []);

  // Map world coordinates to SVG viewBox (X: 0..100m -> 0..200, Y: -5..10m -> 100..0)
  const mapX = (dist) => (dist / 100) * 200;
  const mapY = (h) => 100 - ((h + 5) / 15) * 100;

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;
    const dist = Math.round(nx * 100 * 10) / 10;
    const h = Math.round((10 - ny * 15) * 10) / 10;

    let cls = 'Road';
    if (dist >= 58 && dist <= 76 && h > 1.5) cls = 'Tree Canopy';
    else if (dist >= 38 && dist <= 46 && h > -1.5 && h < 1.5) cls = 'Vehicle';
    else if (dist >= 94) cls = 'Building';
    else if (dist <= 18 && h > -1.5) cls = 'Pedestrian';

    setHoverInfo({ dist, h, cls, px: nx * 100, py: ny * 100 });
  };

  const handleMouseLeave = () => setHoverInfo(null);

  return (
    <div className="bg-[#050a15] border border-[#142646] rounded-lg p-2.5 flex-1 flex flex-col select-none relative overflow-hidden shadow-lg">
      {/* Card Title */}
      <div className="text-[11.5px] font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>Elevation Profile (Front View)</span>
      </div>

      {/* Main Coordinate Plot Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Upper Row: Y Axis + Center Canvas */}
        <div className="flex-1 flex flex-row items-stretch gap-1 min-h-0">
          {/* Y Axis Column: 10, Height (m), 5, 0, -5 */}
          <div className="w-5 flex flex-col justify-between items-end text-[8.5px] font-mono text-[#8299b8] py-0.5 shrink-0 pr-0.5">
            <span>10</span>
            <span className="text-[8px] transform -rotate-90 origin-center text-[#9bb3d1] font-sans font-medium -my-1">
              Height (m)
            </span>
            <span>5</span>
            <span>0</span>
            <span>-5</span>
          </div>

          {/* Center Profile Scatter Plot matching Reference Image */}
          <div
            className="flex-1 h-full bg-[#02050c] border border-[#142646] rounded relative overflow-hidden cursor-crosshair"
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            <svg viewBox="0 0 200 100" className="w-full h-full" preserveAspectRatio="none">
              {/* Subtle Dark Blue Grid Lines */}
              <line x1="0" y1={mapY(10)} x2="200" y2={mapY(10)} stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1="0" y1={mapY(5)} x2="200" y2={mapY(5)} stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1="0" y1={mapY(0)} x2="200" y2={mapY(0)} stroke="#1a355e" strokeWidth="0.9" /> {/* Height = 0 Ground Datum */}
              <line x1="0" y1={mapY(-5)} x2="200" y2={mapY(-5)} stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />

              <line x1={mapX(20)} y1="0" x2={mapX(20)} y2="100" stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1={mapX(40)} y1="0" x2={mapX(40)} y2="100" stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1={mapX(60)} y1="0" x2={mapX(60)} y2="100" stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1={mapX(80)} y1="0" x2={mapX(80)} y2="100" stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />
              <line x1={mapX(100)} y1="0" x2={mapX(100)} y2="100" stroke="#11223e" strokeWidth="0.7" strokeDasharray="3 3" />

              {/* Render High-Density Scatter Points */}
              {profileScatter.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={mapX(pt.x)}
                  cy={mapY(pt.y)}
                  r={pt.r}
                  fill={pt.color}
                  opacity="0.9"
                />
              ))}
            </svg>

            {/* Interactive Crosshair & Tooltip */}
            {hoverInfo && (
              <>
                <div
                  className="absolute top-0 bottom-0 border-l border-white/40 pointer-events-none"
                  style={{ left: `${hoverInfo.px}%` }}
                />
                <div
                  className="absolute left-0 right-0 border-t border-white/40 pointer-events-none"
                  style={{ top: `${hoverInfo.py}%` }}
                />
                <div
                  className="absolute bg-[#0b162c]/95 border border-[#38bdf8]/60 text-white text-[8px] font-mono px-1.5 py-0.5 rounded shadow pointer-events-none z-10 whitespace-nowrap"
                  style={{
                    left: `${Math.min(65, Math.max(5, hoverInfo.px + 4))}%`,
                    top: `${Math.min(75, Math.max(5, hoverInfo.py + 4))}%`,
                  }}
                >
                  Dist:{hoverInfo.dist}m | H:{hoverInfo.h > 0 ? `+${hoverInfo.h}` : hoverInfo.h}m ({hoverInfo.cls})
                </div>
              </>
            )}
          </div>
        </div>

        {/* Lower Row: X Axis at Bottom: 0, 20, 40, 60, 80, 100, Distance (m) / Ego Marker */}
        <div className="flex flex-row items-start gap-1 pt-0.5 select-none">
          {/* Spacer matching Y-axis column width */}
          <div className="w-5 shrink-0" />

          {/* X Axis under Canvas */}
          <div className="flex-1 flex flex-col items-center">
            <div className="w-full flex justify-between text-[8.5px] font-mono text-[#8299b8] px-0.5">
              <span>0</span>
              <span>20</span>
              <span>40</span>
              <span>60</span>
              <span>80</span>
              <span>100</span>
            </div>
            <div className="flex flex-col items-center -mt-0.5">
              <span className="text-[8px] text-[#9bb3d1] font-sans font-medium">Distance (m)</span>
              <span className="text-[7.5px] text-white -mt-0.5 font-bold leading-none">▲</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
