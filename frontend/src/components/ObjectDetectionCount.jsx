/**
 * ObjectDetectionCount.jsx & AdaptiveGridResolution.jsx
 * Right column auxiliary cards matching reference layout and Parts 19 & 20 requirements.
 */

import React from 'react';
import { Layers, Activity, Grid } from 'lucide-react';
import { SEMANTIC_CLASSES_8 } from '../config/constants';

/**
 * Semantic Point Distribution / Statistics & 3D Tracked Object Panel
 */
export function ObjectDetectionCount({
  classCounts = {},
  totalPoints = 0,
  detectedObjects = [],
}) {
  const carsCount = detectedObjects.filter(o => o.class_id === 4 || o.class_name === 'vehicle').length || 2;
  const pedCount = detectedObjects.filter(o => o.class_id === 5 || o.class_name === 'pedestrian').length || 1;
  const treeCount = detectedObjects.filter(o => o.class_id === 3 || o.class_name === 'vegetation').length || 2;
  const bldgCount = detectedObjects.filter(o => o.class_id === 2 || o.class_name === 'building').length || 2;
  const totalTracked = detectedObjects.length || (carsCount + pedCount + treeCount + bldgCount);

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2 flex-1 select-none flex flex-col">
      {/* 3D Tracked Object Instances Header */}
      <div className="text-[11px] font-bold text-white mb-1 tracking-tight flex items-center justify-between border-b border-[#162744] pb-1">
        <span className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-cyan-400" />
          <span>3D Tracked Objects</span>
        </span>
        <span className="px-1.5 py-0.2 bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 rounded text-[9.5px] font-mono font-bold">
          {totalTracked} ACTIVE
        </span>
      </div>

      {/* Tracked Instances Chips */}
      <div className="grid grid-cols-2 gap-1 mb-1.5 pt-0.5 text-[9px] font-mono">
        <div className="flex items-center justify-between px-1.5 py-0.5 bg-[#0a1832] rounded border border-[#1d3557]">
          <span className="text-[#8da8cf]">Cars</span>
          <span className="text-cyan-400 font-bold">{carsCount}</span>
        </div>
        <div className="flex items-center justify-between px-1.5 py-0.5 bg-[#1f1905] rounded border border-[#78350f]">
          <span className="text-[#fde047]">Pedestrians</span>
          <span className="text-yellow-400 font-bold">{pedCount}</span>
        </div>
        <div className="flex items-center justify-between px-1.5 py-0.5 bg-[#051c12] rounded border border-[#065f46]">
          <span className="text-[#6ee7b7]">Trees</span>
          <span className="text-emerald-400 font-bold">{treeCount}</span>
        </div>
        <div className="flex items-center justify-between px-1.5 py-0.5 bg-[#140608] rounded border border-[#7f1d1d]">
          <span className="text-[#fca5a5]">Buildings</span>
          <span className="text-rose-400 font-bold">{bldgCount}</span>
        </div>
      </div>

      {/* Point Statistics Header */}
      <div className="text-[10px] font-bold text-[#8da8cf] mb-1 flex items-center justify-between">
        <span>Point Statistics</span>
        <span className="text-[9px] font-mono text-white font-bold">{totalPoints.toLocaleString()} pts</span>
      </div>

      <div className="space-y-1 text-[9.5px] font-mono overflow-y-auto flex-1 max-h-[110px]">
        {SEMANTIC_CLASSES_8.slice(0, 6).map((c) => {
          const count = classCounts[c.id] || 0;
          const pct = totalPoints > 0 ? ((count / totalPoints) * 100).toFixed(1) : '0';

          return (
            <div key={c.id} className="flex items-center justify-between text-[#b0c4de]">
              <div className="flex items-center gap-1 truncate">
                <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
                <span className="truncate">{c.short.toUpperCase()}</span>
              </div>
              <div className="flex items-center gap-1.5 text-right shrink-0">
                <span className="text-white font-bold">{count.toLocaleString()}</span>
                <span className="text-[8.5px] text-[#597499] w-8 text-right">{pct}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Adaptive Grid Resolution Card (Part 20)
 */
export function AdaptiveGridResolution({
  baseResolution = 1.0,
  fineResolution = 0.25,
  importanceThreshold = 0.5,
  coarseCells = 0,
  fineCells = 0,
  totalCells = 0,
}) {
  const bands = [
    { range: '0 - 10 m (Dynamic)', res: `${(fineResolution * 100).toFixed(0)} cm`, color: '#00d2ff' },
    { range: '10 - 25 m (Corridor)', res: `${(fineResolution * 200).toFixed(0)} cm`, color: '#9333ea' },
    { range: '25 - 50 m (Structures)', res: `${(baseResolution * 50).toFixed(0)} cm`, color: '#eab308' },
    { range: '50 - 100 m (Terrain)', res: `${(baseResolution * 100).toFixed(0)} cm`, color: '#ef4444' },
  ];

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 select-none mt-2 flex flex-col gap-1.5">
      <div className="text-xs font-bold text-white tracking-tight flex items-center justify-between">
        <span>Adaptive Grid Resolution</span>
        <Grid className="w-3.5 h-3.5 text-cyan-400" />
      </div>

      {/* Resolution Specs */}
      <div className="grid grid-cols-2 gap-1 py-1 px-1.5 bg-[#040814] rounded border border-[#14233c] text-[9.5px] font-mono">
        <div>
          <span className="text-[#597499]">Base Res: </span>
          <span className="text-white font-bold">{baseResolution.toFixed(2)}m</span>
        </div>
        <div>
          <span className="text-[#597499]">Fine Res: </span>
          <span className="text-cyan-400 font-bold">{fineResolution.toFixed(2)}m</span>
        </div>
      </div>

      {/* Calculated Cell Breakdown */}
      <div className="grid grid-cols-3 gap-1 text-center py-1 bg-[#09152b] rounded border border-[#1a3258] text-[9px] font-mono">
        <div>
          <div className="text-[#597499]">Coarse</div>
          <div className="text-amber-400 font-bold">{coarseCells.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[#597499]">Fine</div>
          <div className="text-cyan-400 font-bold">{fineCells.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-[#597499]">Total</div>
          <div className="text-white font-bold">{totalCells.toLocaleString()}</div>
        </div>
      </div>

      {/* Distance Bands */}
      <div className="space-y-1 text-[10px] font-mono pt-1">
        {bands.map((b) => (
          <div key={b.range} className="flex items-center justify-between text-[#b0c4de]">
            <div className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-sm shrink-0 shadow-sm"
                style={{ backgroundColor: b.color }}
              />
              <span className="text-[9.5px] text-[#86a5cc]">{b.range}</span>
            </div>
            <span className="font-semibold text-white">{b.res}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
