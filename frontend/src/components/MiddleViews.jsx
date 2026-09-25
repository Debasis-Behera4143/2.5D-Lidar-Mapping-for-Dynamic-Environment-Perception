/**
 * MiddleViews.jsx
 * The three horizontal cards directly below the main 3D viewer matching the reference screenshot:
 * 1. 2.5D Elevation Map (Side/Front View) with vertical colorbar (0.0 to 5.0m)
 * 2. Semantic Map (Top View) 2D BEV raster with mini legend
 * 3. Elevation Profile (Front View) Distance (0-100m) vs Height (0-10m)
 */

import React, { useMemo } from 'react';
import { SEMANTIC_CLASSES_8, CLASS_COLORS } from '../config/constants';
import Three25DElevationViewer from './Three25DElevationViewer';

/**
 * 1. 2.5D Elevation Map (Side/Front View)
 */
export function SideFrontElevationView({ points = [], labels = [] }) {
  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none relative overflow-hidden">
      <div className="text-xs font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>2.5D Elevation Map (Side/Front View)</span>
        <span className="text-[9px] font-mono text-[#5d7d9f]">Turbo Height</span>
      </div>

      <div className="flex-1 w-full h-full relative">
        <Three25DElevationViewer points={points} labels={labels} />
      </div>
    </div>
  );
}

/**
 * 2. Semantic Map (Top View) - 2D Bird's Eye View Grid
 */
export function SemanticMapTopView({
  points = [],
  labels = [],
  adaptiveMap = null,
}) {
  // Generate 2D BEV Top-Down raster grid from actual points or adaptive map cells
  const bevCells = useMemo(() => {
    if (adaptiveMap?.cells && adaptiveMap.cells.length > 0) {
      return adaptiveMap.cells.slice(0, 120);
    }
    // Fallback compute from points
    if (!points || points.length === 0) return [];
    const step = Math.max(1, Math.floor(points.length / 100));
    const sample = [];
    for (let i = 0; i < points.length; i += step) {
      sample.push({
        center_x: points[i][0],
        center_y: points[i][1],
        dominant_class: labels[i] !== undefined ? labels[i] : 0,
      });
    }
    return sample;
  }, [points, labels, adaptiveMap]);

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>Semantic Map (Top View)</span>
        <span className="text-[9px] font-mono text-[#5d7d9f]">2D BEV</span>
      </div>

      <div className="flex-1 flex items-center justify-between gap-2.5">
        {/* 2D Intersection BEV Raster Canvas */}
        <div className="w-36 h-28 bg-[#030712] border border-[#14233c] rounded relative overflow-hidden p-1 flex items-center justify-center">
          <svg viewBox="0 0 100 100" className="w-full h-full">
            {/* Background */}
            <rect x="0" y="0" width="100" height="100" fill="#050c18" />

            {/* Render actual top-down BEV cells */}
            {bevCells.map((c, idx) => {
              // Map (-20..20 lateral, -10..50 longitudinal) to (0..100 SVG coords)
              const svgX = 50 + (c.center_y || 0) * 2.2;
              const svgY = 70 - (c.center_x || 0) * 1.3;
              const col = CLASS_COLORS[c.dominant_class] || '#1d64f2';
              return (
                <rect
                  key={idx}
                  x={Math.max(2, Math.min(94, svgX - 2.5))}
                  y={Math.max(2, Math.min(94, svgY - 2.5))}
                  width={5}
                  height={5}
                  fill={col}
                  opacity={0.85}
                  rx={0.5}
                />
              );
            })}

            {/* Ego Car Marker */}
            <rect x="47" y="65" width="6" height="10" rx="1.5" fill="#ffffff" stroke="#38bdf8" strokeWidth="0.8" />
          </svg>
        </div>

        {/* Mini 2-Column Legend */}
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-[#9bb3d1] flex-1">
          {SEMANTIC_CLASSES_8.map((l) => (
            <div key={l.id} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: l.color }} />
              <span className="truncate text-[9.5px]">{l.name.split(' ')[0]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 3. Elevation Profile (Front View)
 */
export function ElevationProfileFrontView({
  points = [],
  profileData = null,
}) {
  // Compute profile curve from points or use provided profile
  const { pathD, fillD, maxH } = useMemo(() => {
    let dists = [];
    let heights = [];

    if (profileData?.distance_m && profileData?.height_m) {
      dists = profileData.distance_m;
      heights = profileData.height_m;
    } else if (points && points.length > 0) {
      // Bin points along distance X (0 to 60m) and compute max height
      const numBins = 30;
      const binMaxH = new Array(numBins).fill(0.1);
      const step = Math.max(1, Math.floor(points.length / 1000));
      for (let i = 0; i < points.length; i += step) {
        const x = points[i][0];
        const z = points[i][2];
        if (x >= 0 && x <= 60) {
          const binIdx = Math.min(numBins - 1, Math.floor((x / 60) * numBins));
          binMaxH[binIdx] = Math.max(binMaxH[binIdx], z);
        }
      }
      dists = Array.from({ length: numBins }, (_, i) => (i / numBins) * 100);
      heights = binMaxH;
    } else {
      // Reference baseline default
      dists = [0, 15, 30, 45, 60, 75, 90, 100];
      heights = [0.2, 1.4, 2.8, 4.5, 7.8, 3.2, 1.8, 0.4];
    }

    const maxVal = Math.max(5.0, ...heights);
    const svgW = 300;
    const svgH = 65;

    const pts = dists.map((d, i) => {
      const h = heights[i] !== undefined ? heights[i] : 0.2;
      const px = (d / 100) * svgW;
      const py = svgH - (h / 10) * (svgH - 5);
      return `${px.toFixed(1)},${py.toFixed(1)}`;
    });

    const pD = `M ${pts.join(' L ')}`;
    const fD = `M 0,${svgH} L ${pts.join(' L ')} L ${svgW},${svgH} Z`;

    return { pathD: pD, fillD: fD, maxH: maxVal.toFixed(1) };
  }, [points, profileData]);

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>Elevation Profile (Front View)</span>
        <span className="text-[9px] font-mono text-[#5d7d9f]">Max: {maxH}m</span>
      </div>

      <div className="flex-1 flex flex-col justify-between">
        {/* SVG Rainbow Elevation Envelope */}
        <div className="h-24 w-full relative flex items-end">
          <svg viewBox="0 0 300 70" preserveAspectRatio="none" className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="elevRainbow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#00d2ff" />
                <stop offset="30%" stopColor="#eab308" />
                <stop offset="65%" stopColor="#ef4444" />
                <stop offset="85%" stopColor="#d946ef" />
                <stop offset="100%" stopColor="#00d2ff" />
              </linearGradient>
            </defs>

            {/* Filled Mountain Peak Profile */}
            <path d={fillD} fill="url(#elevRainbow)" opacity="0.9" />

            {/* Outline Stroke */}
            <path d={pathD} fill="none" stroke="#ffffff" strokeWidth="1.2" opacity="0.85" />

            {/* Baseline Grid */}
            <line x1="0" y1="65" x2="300" y2="65" stroke="#1f375b" strokeWidth="1" />
          </svg>

          {/* Left Y Axis Values */}
          <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-[8px] font-mono text-[#6e8db3]">
            <span>10m</span>
            <span>5m</span>
            <span>0m</span>
          </div>
        </div>

        {/* X Axis: Distance (m) */}
        <div className="flex justify-between text-[8px] font-mono text-[#6e8db3] px-2 pt-0.5 border-t border-[#162744]">
          <span>0</span>
          <span>20</span>
          <span>40</span>
          <span>60</span>
          <span>80</span>
          <span>100</span>
        </div>
        <div className="text-center text-[9px] font-mono text-[#89a7cc] -mt-0.5">
          Distance (m)
        </div>
      </div>
    </div>
  );
}
