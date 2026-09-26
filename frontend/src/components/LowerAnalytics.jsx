/**
 * LowerAnalytics.jsx
 * Bottom section cards matching the reference screenshot:
 * 1. Performance Metrics (4 Glowing Circular Ring Gauges)
 * 2. System Logs (Live Terminal)
 * 3. Grid Comparison (Uniform Grid vs Adaptive Grid)
 * 4. What This Dashboard Shows (Footer Summary Legend Bar)
 */

import React from 'react';
import { Target, Car, TreePine, Layers, ShieldAlert } from 'lucide-react';

/**
 * 1. Performance Metrics with 4 Glowing Circular Ring Gauges
 */
export function PerformanceMetricsGauges({
  totalPoints = 25000,
  uniformCells = 1600,
  adaptiveCells = 640,
  inferenceMs = null,
  mappingMs = null,
}) {
  const reductionPct = uniformCells > 0
    ? Math.max(0, Math.min(100, Math.round(((uniformCells - adaptiveCells) / uniformCells) * 100)))
    : 60;

  const gauges = [
    {
      label: 'Cell Reduction',
      value: `${reductionPct}%`,
      sub: 'Memory Saving',
      color: '#10b981',
      ringPct: reductionPct,
    },
    {
      label: 'Adaptive Cells',
      value: adaptiveCells.toLocaleString(),
      sub: 'Quadtree Cells',
      color: '#00d2ff',
      ringPct: Math.min(100, Math.round((adaptiveCells / Math.max(1, uniformCells)) * 100)),
    },
    {
      label: 'Uniform Cells',
      value: uniformCells.toLocaleString(),
      sub: 'Fixed Grid',
      color: '#a855f7',
      ringPct: 100,
    },
    {
      label: 'LiDAR Points',
      value: totalPoints >= 1000 ? `${(totalPoints / 1000).toFixed(0)}k` : `${totalPoints}`,
      sub: inferenceMs ? `${inferenceMs} ms` : 'GPU Buffer',
      color: '#f97316',
      ringPct: Math.min(100, Math.round((totalPoints / 50000) * 100)),
    },
  ];

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none min-h-[100px] md:min-h-0">
      <div className="text-xs font-bold text-white mb-1.5 tracking-tight flex items-center justify-between">
        <span>Performance Metrics</span>
        <span className="text-[9px] font-mono text-[#5d7d9f]">
          {inferenceMs ? `Latency: ${inferenceMs}ms` : 'GPU Accelerated'}
        </span>
      </div>

      <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-1.5 items-center">
        {gauges.map((g) => {
          const radius = 22;
          const circumference = 2 * Math.PI * radius;
          const strokeDashoffset = circumference - (g.ringPct / 100) * circumference;

          return (
            <div key={g.label} className="flex flex-col items-center text-center">
              <div className="relative w-14 h-14 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  {/* Background Track Ring */}
                  <circle
                    cx="28"
                    cy="28"
                    r={radius}
                    stroke="#14243b"
                    strokeWidth="3.5"
                    fill="transparent"
                  />
                  {/* Glowing Colored Progress Ring */}
                  <circle
                    cx="28"
                    cy="28"
                    r={radius}
                    stroke={g.color}
                    strokeWidth="3.5"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    fill="transparent"
                  />
                </svg>
                {/* Center Value */}
                <span className="absolute text-[10.5px] font-bold font-mono text-white">
                  {g.value}
                </span>
              </div>
              <span className="text-[9px] text-[#86a5cc] font-medium leading-tight text-center">
                {g.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * 2. System Logs (Live Terminal with actual logs)
 */
export function SystemLogsPanel({ logs = [] }) {
  const defaultLogs = [
    { time: '14:32:10', text: 'Loaded frame 000000 (25,000 points)' },
    { time: '14:32:11', text: 'Point cloud buffer initialized on GPU' },
    { time: '14:32:13', text: 'RandLA-Net inference completed (8 classes)' },
    { time: '14:32:15', text: 'Adaptive 2.5D grid generated (640 cells)' },
    { time: '14:32:16', text: '2.5D elevation map synchronized' },
    { time: '14:32:17', text: 'Ready (Analysis Ready)' },
  ];

  const displayLogs = logs && logs.length > 0 ? logs : defaultLogs;

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>System Logs</span>
        <span className="text-[9px] font-mono text-cyan-400">Live Stream</span>
      </div>
      <div className="flex-1 bg-[#030712] border border-[#14233c] rounded p-2 overflow-y-auto font-mono text-[9.5px] space-y-0.5">
        {displayLogs.map((l, i) => (
          <div key={i} className="flex gap-2 text-[#99b5d6]">
            <span className="text-[#51749c]">{l.time || '14:32'}</span>
            <span className="text-[#c8daf2]">{l.text || l.msg || l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * 3. Grid Comparison (Uniform vs Adaptive)
 */
export function GridComparisonPanel({
  uniformCells = 1600,
  adaptiveCells = 640,
  baseResolution = 1.0,
  fineResolution = 0.25,
}) {
  const reductionPct = uniformCells > 0
    ? (((uniformCells - adaptiveCells) / uniformCells) * 100).toFixed(1)
    : '60.0';

  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-1 tracking-tight flex items-center justify-between">
        <span>Grid Comparison</span>
        <span className="text-[9px] font-mono text-emerald-400 font-bold">-{reductionPct}% Reduction</span>
      </div>

      <div className="flex-1 grid grid-cols-2 gap-2 text-[10px] font-mono">
        {/* Uniform Grid Preview */}
        <div className="flex flex-col">
          <div className="flex justify-between text-[#89a7cc] mb-0.5 text-[8.5px]">
            <span>Uniform Grid</span>
            <span className="text-white font-bold">{uniformCells.toLocaleString()} cells</span>
          </div>
          <div className="flex-1 bg-[#040813] border border-[#1b345b] rounded p-1 flex items-center justify-center relative overflow-hidden">
            <svg viewBox="0 0 80 50" className="w-full h-full">
              <rect width="80" height="50" fill="#10b981" opacity="0.4" />
              <rect x="25" y="0" width="30" height="50" fill="#1d64f2" opacity="0.8" />
              {Array.from({ length: 14 }).map((_, i) => (
                <line key={i} x1={i * 6} y1="0" x2={i * 6} y2="50" stroke="#00d2ff" strokeWidth="0.4" opacity="0.7" />
              ))}
              {Array.from({ length: 9 }).map((_, i) => (
                <line key={i} x1="0" y1={i * 6} x2="80" y2={i * 6} stroke="#00d2ff" strokeWidth="0.4" opacity="0.7" />
              ))}
            </svg>
          </div>
        </div>

        {/* Adaptive Grid Preview */}
        <div className="flex flex-col">
          <div className="flex justify-between text-[#89a7cc] mb-0.5 text-[8.5px]">
            <span>Adaptive Grid</span>
            <span className="text-cyan-400 font-bold">{adaptiveCells.toLocaleString()} cells</span>
          </div>
          <div className="flex-1 bg-[#040813] border border-[#1b345b] rounded p-1 flex items-center justify-center relative overflow-hidden">
            <svg viewBox="0 0 80 50" className="w-full h-full">
              <rect width="80" height="50" fill="#10b981" opacity="0.4" />
              <rect x="25" y="0" width="30" height="50" fill="#1d64f2" opacity="0.8" />
              {/* Fine mesh center road */}
              {Array.from({ length: 10 }).map((_, i) => (
                <line key={i} x1={25 + i * 3} y1="0" x2={25 + i * 3} y2="50" stroke="#00d2ff" strokeWidth="0.5" />
              ))}
              {/* Coarse mesh outside */}
              <line x1="12" y1="0" x2="12" y2="50" stroke="#eab308" strokeWidth="0.8" />
              <line x1="68" y1="0" x2="68" y2="50" stroke="#ef4444" strokeWidth="0.8" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 4. Footer Summary Ribbon matching reference screenshot
 */
export function FooterBar() {
  return (
    <footer className="min-h-9 bg-[#040813] border-t border-[#14233c] px-3 md:px-4 py-1.5 md:py-0 flex flex-col md:flex-row items-center justify-between text-xs select-none shrink-0 gap-1 md:gap-0">
      {/* What This Dashboard Shows */}
      <div className="flex items-center gap-2 text-center md:text-left">
        <Target className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span className="font-bold text-white text-[10px] md:text-[11px]">What This Dashboard Shows</span>
        <span className="hidden sm:inline text-[10.5px] text-[#718eb3]">
          A real-time view of the LiDAR scene, semantic understanding, adaptive 2.5D mapping and system performance.
        </span>
      </div>

      {/* Legend Badges */}
      <div className="hidden lg:flex items-center gap-4 text-[10px] text-[#86a5cc]">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-[#ef4444]" />
          <span>Left Wall (Non-drivable)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Car className="w-3 h-3 text-[#d946ef]" />
          <span>Front Vehicle (Dynamic)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <TreePine className="w-3 h-3 text-[#10b981]" />
          <span>Right Tree (Static)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Layers className="w-3 h-3 text-[#00d2ff]" />
          <span>Grid Resolution (Variable)</span>
        </div>
        <div className="flex items-center gap-1.5 text-white font-semibold">
          <span>Map Type: Semantic 2.5D Elevation</span>
        </div>
      </div>
    </footer>
  );
}
