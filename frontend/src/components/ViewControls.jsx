/**
 * ViewControls.jsx
 * Viewport display modes, point size, height exaggeration, and layer visibility.
 */

import React from 'react';
import { Eye, EyeOff, Layers, Sliders, Move3d } from 'lucide-react';
import { COLOR_MODES, VIEW_MODES } from '../app/config';

export default function ViewControls({
  colorMode,
  onChangeColorMode,
  viewMode,
  onChangeViewMode,
  pointSize,
  onChangePointSize,
  heightExaggeration = 1.0,
  onChangeHeightExaggeration,
  showPoints,
  onTogglePoints,
  showHeightMap,
  onToggleHeightMap,
  showGrid,
  onToggleGrid,
  showRangeRings,
  onToggleRangeRings,
}) {
  return (
    <div className="tech-card p-3 space-y-2.5 select-none text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>Viewport Controls</span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono-num">Rendering</span>
      </div>

      {/* 1. Color Palette Shader */}
      <div className="space-y-1">
        <div className="flex justify-between text-slate-400 text-[11px]">
          <span>Point Color Shader:</span>
        </div>
        <select
          value={colorMode}
          onChange={(e) => onChangeColorMode(e.target.value)}
          className="w-full bg-[#060a17] border border-slate-800 text-slate-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-blue-500 font-mono-num"
        >
          {COLOR_MODES.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      {/* 2. Layer Visibility Toggles */}
      <div className="grid grid-cols-2 gap-1.5 text-[10px]">
        <button
          onClick={() => onTogglePoints(!showPoints)}
          className={`p-1.5 rounded flex items-center justify-between border ${
            showPoints
              ? 'bg-blue-950/40 border-blue-500/40 text-blue-300'
              : 'bg-[#050811] border-slate-800 text-slate-500'
          }`}
        >
          <span>LiDAR Points</span>
          {showPoints ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
        </button>

        <button
          onClick={() => onToggleHeightMap(!showHeightMap)}
          className={`p-1.5 rounded flex items-center justify-between border ${
            showHeightMap
              ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300'
              : 'bg-[#050811] border-slate-800 text-slate-500'
          }`}
        >
          <span>2.5D Adaptive Grid</span>
          {showHeightMap ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
        </button>

        <button
          onClick={() => onToggleRangeRings(!showRangeRings)}
          className={`p-1.5 rounded flex items-center justify-between border ${
            showRangeRings
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
              : 'bg-[#050811] border-slate-800 text-slate-500'
          }`}
        >
          <span>Metric Rings</span>
          {showRangeRings ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
        </button>

        <button
          onClick={() => onToggleGrid(!showGrid)}
          className={`p-1.5 rounded flex items-center justify-between border ${
            showGrid
              ? 'bg-purple-950/40 border-purple-500/40 text-purple-300'
              : 'bg-[#050811] border-slate-800 text-slate-500'
          }`}
        >
          <span>Ground Grid</span>
          {showGrid ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
        </button>
      </div>

      {/* 3. Point Size & Height Exaggeration Sliders */}
      <div className="space-y-1.5 pt-1 border-t border-slate-800/80 font-mono-num text-[10px]">
        <div className="space-y-0.5">
          <div className="flex justify-between">
            <span className="text-slate-400">Point Size:</span>
            <span className="text-cyan-400 font-bold">{pointSize.toFixed(1)} px</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="6.0"
            step="0.5"
            value={pointSize}
            onChange={(e) => onChangePointSize(parseFloat(e.target.value))}
            className="w-full accent-blue-500 h-1 bg-slate-800 rounded cursor-pointer"
          />
        </div>

        {onChangeHeightExaggeration && (
          <div className="space-y-0.5">
            <div className="flex justify-between">
              <span className="text-slate-400">Height Scale (Z):</span>
              <span className="text-emerald-400 font-bold">{heightExaggeration.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="3.0"
              step="0.2"
              value={heightExaggeration}
              onChange={(e) => onChangeHeightExaggeration(parseFloat(e.target.value))}
              className="w-full accent-emerald-500 h-1 bg-slate-800 rounded cursor-pointer"
            />
          </div>
        )}
      </div>
    </div>
  );
}
