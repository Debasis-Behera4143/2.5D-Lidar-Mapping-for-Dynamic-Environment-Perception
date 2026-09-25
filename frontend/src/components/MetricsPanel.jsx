/**
 * MetricsPanel.jsx
 * Quantitative Efficiency Benchmarks calculated purely from pipeline results.
 * No fabricated values; displays 'N/A' when metrics have not been generated.
 */

import React from 'react';
import { TrendingDown, HardDrive, Zap, Layers } from 'lucide-react';

export default function MetricsPanel({
  comparison = null,
  adaptiveMap = null,
  uniformMap = null,
  inferenceLatencyMs = null,
  mappingLatencyMs = null,
}) {
  const compData = comparison?.comparison || {};
  const uni = comparison?.uniform || uniformMap || {};
  const ada = comparison?.adaptive || adaptiveMap || {};

  const hasReduction = typeof compData.cell_count_reduction_percent === 'number';
  const cellReduction = hasReduction ? compData.cell_count_reduction_percent : null;
  const memReduction = typeof compData.estimated_memory_reduction_percent === 'number'
    ? compData.estimated_memory_reduction_percent
    : null;

  const uniCells = uni.cell_count;
  const adaCells = ada.cell_count;
  const coarseCells = ada.coarse_cell_count;
  const fineCells = ada.fine_cell_count;

  return (
    <div className="tech-card p-3 space-y-3 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
          <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
          <span>Pipeline Benchmarks</span>
        </div>
        {cellReduction !== null ? (
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 font-mono-num font-bold">
            {cellReduction >= 0 ? `-${cellReduction.toFixed(1)}%` : `+${cellReduction.toFixed(1)}%`} CELLS
          </span>
        ) : (
          <span className="text-[10px] text-slate-500 font-mono-num">MEASURED</span>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-2 text-center font-mono-num">
        {/* Cell Count Savings */}
        <div className="bg-[#050914] p-2 rounded border border-slate-800">
          <div className="text-[10px] text-slate-400">CELL REDUCTION</div>
          <div className="text-sm font-bold text-emerald-400">
            {cellReduction !== null ? `${cellReduction.toFixed(1)}%` : 'N/A'}
          </div>
          <div className="text-[9px] text-slate-500">
            {typeof adaCells === 'number' && typeof uniCells === 'number'
              ? `${adaCells.toLocaleString()} vs ${uniCells.toLocaleString()}`
              : 'Execute mapping'}
          </div>
        </div>

        {/* Estimated Struct Memory */}
        <div className="bg-[#050914] p-2 rounded border border-slate-800">
          <div className="text-[10px] text-slate-400">EST. MEMORY</div>
          <div className="text-sm font-bold text-cyan-400">
            {typeof ada.estimated_memory_kb === 'number'
              ? `${ada.estimated_memory_kb.toFixed(1)} KB`
              : (typeof adaCells === 'number' ? `${((adaCells * 64) / 1024).toFixed(1)} KB` : 'N/A')}
          </div>
          <div className="text-[9px] text-slate-500">
            {memReduction !== null ? `${memReduction.toFixed(1)}% struct reduction` : '64 bytes/cell model'}
          </div>
        </div>
      </div>

      {/* Latency & Cell Distribution */}
      <div className="bg-[#060a17] p-2.5 rounded border border-slate-800/80 space-y-1.5 text-[11px] font-mono-num">
        <div className="flex justify-between text-slate-400">
          <span>Coarse Base Cells:</span>
          <span className="text-slate-200 font-bold">
            {typeof coarseCells === 'number' ? coarseCells.toLocaleString() : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Fine Subdivided Cells:</span>
          <span className="text-cyan-300 font-bold">
            {typeof fineCells === 'number' ? fineCells.toLocaleString() : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Inference Latency:</span>
          <span className="text-slate-200 font-bold">
            {typeof inferenceLatencyMs === 'number' ? `${inferenceLatencyMs} ms` : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Mapping Latency:</span>
          <span className="text-slate-200 font-bold">
            {typeof mappingLatencyMs === 'number' ? `${mappingLatencyMs} ms` : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
