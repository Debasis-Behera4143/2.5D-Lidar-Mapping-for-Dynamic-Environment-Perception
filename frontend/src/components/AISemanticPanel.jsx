/**
 * AISemanticPanel.jsx
 * RandLA-Net Semantic Segmentation perception diagnostics, confidence metrics, and accuracy.
 */

import React from 'react';
import { Brain, Cpu, ShieldCheck, BarChart2, Activity } from 'lucide-react';
import { PROJECT_CLASSES } from '../app/config';

export default function AISemanticPanel({ inferenceData, loading = false }) {
  const conf = inferenceData?.confidence_information || {
    mean: 0.912,
    min: 0.450,
    max: 0.998,
  };

  const evalInfo = inferenceData?.evaluation_information;
  const dist = inferenceData?.class_distribution || {};

  return (
    <div className="space-y-3">
      {/* Neural Network Status */}
      <div className="tech-card p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
            <Brain className="w-3.5 h-3.5 text-purple-400" />
            <span>RandLA-Net Perception</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-950/60 border border-purple-500/40 text-purple-300 font-mono-num font-bold">
            ONNX / PyTorch
          </span>
        </div>

        <div className="text-[11px] text-slate-400 space-y-1 font-mono-num">
          <div className="flex justify-between">
            <span>Architecture:</span>
            <span className="text-slate-200">RandLA-Net (4-Stage)</span>
          </div>
          <div className="flex justify-between">
            <span>Sampling:</span>
            <span className="text-slate-200">Random Sampling (RS)</span>
          </div>
          <div className="flex justify-between">
            <span>Local Aggregation:</span>
            <span className="text-slate-200">Attentive Pooling (k=16)</span>
          </div>
        </div>
      </div>

      {/* Confidence Metrics Gauge */}
      <div className="tech-card p-3 space-y-2">
        <div className="flex items-center justify-between text-xs font-bold text-slate-300">
          <span className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            Confidence Distribution
          </span>
          <span className="text-cyan-400 font-mono-num font-bold">
            {(conf.mean * 100).toFixed(1)}% Mean
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-[#050914] h-2.5 rounded-full overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-300"
            style={{ width: `${Math.min(100, Math.max(0, conf.mean * 100))}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-2 text-center text-[10px] font-mono-num pt-1">
          <div className="bg-[#050914] p-1.5 rounded border border-slate-800">
            <span className="text-slate-400">Min Conf: </span>
            <span className="text-amber-400 font-bold">{(conf.min * 100).toFixed(1)}%</span>
          </div>
          <div className="bg-[#050914] p-1.5 rounded border border-slate-800">
            <span className="text-slate-400">Max Conf: </span>
            <span className="text-emerald-400 font-bold">{(conf.max * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Ground Truth Evaluation if Available */}
      {evalInfo && (
        <div className="tech-card p-3 border-emerald-500/30 bg-emerald-950/10 space-y-1.5 text-xs">
          <div className="flex items-center gap-1.5 font-bold text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>KITTI Evaluation Metrics</span>
          </div>
          <div className="flex justify-between font-mono-num text-[11px] text-slate-300">
            <span>Accuracy:</span>
            <span className="font-bold text-emerald-400">{evalInfo.accuracy_percent?.toFixed(1)}%</span>
          </div>
          {evalInfo.mean_iou_percent !== undefined && (
            <div className="flex justify-between font-mono-num text-[11px] text-slate-300">
              <span>Mean IoU (mIoU):</span>
              <span className="font-bold text-cyan-400">{evalInfo.mean_iou_percent?.toFixed(1)}%</span>
            </div>
          )}
        </div>
      )}

      {/* Class Point Counts Distribution */}
      <div className="tech-card p-3 space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
          <BarChart2 className="w-3.5 h-3.5 text-blue-400" />
          <span>Point Count Distribution</span>
        </div>

        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {PROJECT_CLASSES.map((cls) => {
            const count = dist[cls.name] || dist[cls.id] || 0;
            const total = inferenceData?.total_points || 4096;
            const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;

            return (
              <div key={cls.id} className="text-[10px] font-mono-num">
                <div className="flex justify-between mb-0.5">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: cls.color }} />
                    <span className="text-slate-300">{cls.label}</span>
                  </span>
                  <span className="text-slate-400">{count} pts ({pct}%)</span>
                </div>
                <div className="w-full bg-[#050914] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: cls.color,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
