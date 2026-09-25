/**
 * AdaptiveMappingPanel.jsx
 * Interactive control parameters for 2.5D Adaptive Variable-Resolution Grid Mapping.
 */

import React from 'react';
import { Sliders, Layers, RefreshCw, Zap, Settings2 } from 'lucide-react';

export default function AdaptiveMappingPanel({
  config,
  onChangeConfig,
  onRunMapping,
  loading = false,
}) {
  return (
    <div className="space-y-3 select-none">
      {/* Configuration Header */}
      <div className="tech-card p-3 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            <span>2.5D Grid Resolution Tuning</span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono-num">Member 3 Engine</span>
        </div>

        {/* 1. Base Coarse Resolution */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Coarse Base Res:</span>
            <span className="font-mono-num font-bold text-cyan-400">
              {config.baseResolution?.toFixed(2)} m
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={config.baseResolution}
            onChange={(e) => onChangeConfig({ baseResolution: parseFloat(e.target.value) })}
            className="w-full accent-cyan-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[9px] text-slate-500 font-mono-num">
            <span>0.5m (Dense)</span>
            <span>2.0m (Sparse)</span>
          </div>
        </div>

        {/* 2. Fine Subdivided Resolution */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Fine Subdivided Res:</span>
            <span className="font-mono-num font-bold text-emerald-400">
              {config.fineResolution?.toFixed(2)} m
            </span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.50"
            step="0.05"
            value={config.fineResolution}
            onChange={(e) => onChangeConfig({ fineResolution: parseFloat(e.target.value) })}
            className="w-full accent-emerald-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[9px] text-slate-500 font-mono-num">
            <span>0.10m (High Detail)</span>
            <span>0.50m (Standard)</span>
          </div>
        </div>

        {/* 3. Importance Threshold */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Importance Threshold:</span>
            <span className="font-mono-num font-bold text-amber-400">
              {config.importanceThreshold?.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min="0.10"
            max="0.90"
            step="0.05"
            value={config.importanceThreshold}
            onChange={(e) => onChangeConfig({ importanceThreshold: parseFloat(e.target.value) })}
            className="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[9px] text-slate-500 font-mono-num">
            <span>0.10 (Subdivide All)</span>
            <span>0.90 (Subdivide Few)</span>
          </div>
        </div>

        {/* 4. Motion Compensation Dynamic Threshold */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-slate-300 font-medium">Dynamic Motion Ratio:</span>
            <span className="font-mono-num font-bold text-purple-400">
              {config.dynamicThreshold?.toFixed(2)}
            </span>
          </div>
          <input
            type="range"
            min="0.05"
            max="0.80"
            step="0.05"
            value={config.dynamicThreshold}
            onChange={(e) => onChangeConfig({ dynamicThreshold: parseFloat(e.target.value) })}
            className="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Run Mapping Button */}
        <button
          onClick={onRunMapping}
          disabled={loading}
          className="w-full py-2 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-bold text-xs rounded shadow-lg shadow-blue-500/20 flex items-center justify-center gap-1.5 transition active:scale-[0.98] disabled:opacity-50"
        >
          {loading ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Synthesizing Grid...</span>
            </>
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 fill-white" />
              <span>Update 2.5D Adaptive Map</span>
            </>
          )}
        </button>
      </div>

      {/* Info Card */}
      <div className="tech-card p-2.5 text-[10px] text-slate-400 space-y-1 font-mono-num bg-[#050811]">
        <div className="text-slate-300 font-bold flex items-center gap-1">
          <Settings2 className="w-3 h-3 text-blue-400" />
          <span>Heuristic Weightings:</span>
        </div>
        <div>• Road / Ground: <span className="text-slate-200">Coarse (0.15)</span></div>
        <div>• Obstacles / Vehicles: <span className="text-cyan-300">Fine Subdivided (0.90)</span></div>
        <div>• Pedestrians / Signs: <span className="text-emerald-300">Fine Subdivided (0.95)</span></div>
        <div>• Dynamic moving objects trigger instant quadtree refinement.</div>
      </div>
    </div>
  );
}
