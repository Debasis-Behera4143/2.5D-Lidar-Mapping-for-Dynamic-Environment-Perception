/**
 * SceneOverview.jsx
 * Left Column Pipeline Stack matching the reference screenshot:
 * 1. Scene Overview (Live raw LiDAR point preview thumbnail)
 * 2. AI Semantic Segmentation (RandLA-Net, labels, confidence)
 * 3. Adaptive Grid + 2.5D Mapping (Variable resolution, sliders, UPDATE button)
 */

import React, { useRef, useEffect } from 'react';
import { Brain, Layers, ArrowDown, Sliders } from 'lucide-react';
import { CLASS_COLORS } from '../config/constants';

export default function SceneOverview({
  frameId = '000000',
  pointCount = 0,
  points = [],
  labels = [],
  baseResolution = 1.0,
  fineResolution = 0.25,
  importanceThreshold = 0.5,
  onChangeBaseRes,
  onChangeFineRes,
  onChangeThreshold,
  onUpdateAdaptiveMap,
  isUpdatingMap = false,
}) {
  const canvasRef = useRef(null);

  // Render actual 2D/3D raw LiDAR point cloud projection in the mini canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear background
    ctx.fillStyle = '#030712';
    ctx.fillRect(0, 0, width, height);

    // Draw grid radar circles
    ctx.strokeStyle = '#0f223d';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2, 20, 0, Math.PI * 2);
    ctx.arc(width / 2, height / 2, 40, 0, Math.PI * 2);
    ctx.arc(width / 2, height / 2, 60, 0, Math.PI * 2);
    ctx.stroke();

    if (!points || points.length === 0) {
      // Placeholder dots if no points loaded yet
      ctx.fillStyle = '#38bdf8';
      ctx.font = '9px monospace';
      ctx.fillText('Loading Scan...', width / 2 - 35, height / 2);
      return;
    }

    // Project points (X = forward 0..60, Y = lateral -20..20) onto canvas
    const sampleStep = Math.max(1, Math.floor(points.length / 500));
    const cx = width / 2;
    const cy = height * 0.65;
    const scale = 1.8;

    for (let i = 0; i < points.length; i += sampleStep) {
      const pt = points[i];
      const lbl = labels[i] !== undefined ? labels[i] : 7;
      const col = CLASS_COLORS[lbl] || '#38bdf8';

      // Three.js / KITTI projection: pt[1] lateral (-Y), pt[0] forward (X)
      const px = cx + (pt[1] || 0) * scale;
      const py = cy - (pt[0] || 0) * scale * 0.8;

      if (px >= 0 && px < width && py >= 0 && py < height) {
        ctx.fillStyle = col;
        ctx.fillRect(px, py, 1.2, 1.2);
      }
    }

    // Ego vehicle marker at center
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(cx - 2, cy - 3, 4, 6);
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1;
    ctx.strokeRect(cx - 2, cy - 3, 4, 6);
  }, [points, labels, frameId]);

  return (
    <div className="w-[200px] shrink-0 flex flex-col gap-2 select-none overflow-y-auto pr-0.5">
      {/* 1. Scene Overview & Raw Point Cloud Thumbnail */}
      <div className="bg-[#071123] border border-[#162744] rounded-lg p-2 flex flex-col">
        <div className="text-xs font-bold text-white mb-1.5 flex items-center justify-between">
          <span>Scene Overview</span>
          <span className="text-[9px] font-mono text-[#7896bf] bg-[#0a1830] px-1.5 py-0.5 rounded">
            Frame: {frameId}
          </span>
        </div>

        <div className="w-full h-20 rounded bg-[#030712] border border-[#1b3156] relative overflow-hidden flex items-center justify-center">
          <canvas
            ref={canvasRef}
            width={190}
            height={80}
            className="w-full h-full object-cover"
          />
          <div className="absolute bottom-1 text-[8px] font-mono text-[#7896bf] px-1 bg-[#050b18]/85 rounded">
            Points: {pointCount > 0 ? pointCount.toLocaleString() : 'Loading'}
          </div>
        </div>
        <div className="text-[9px] text-[#5d7d9f] font-medium text-center mt-1">
          Raw LiDAR Point Cloud (3D)
        </div>
      </div>

      {/* Down Arrow 1 */}
      <div className="flex justify-center -my-1 text-[#3b82f6]">
        <ArrowDown className="w-3.5 h-3.5 animate-bounce" />
      </div>

      {/* 2. AI Semantic Segmentation */}
      <div className="bg-[#071123] border border-[#162744] rounded-lg p-2">
        <div className="flex items-center gap-1.5 mb-1.5">
          <div className="w-4 h-4 rounded bg-[#132c54] flex items-center justify-center text-[#38bdf8]">
            <Brain className="w-3 h-3" />
          </div>
          <span className="text-[11px] font-bold text-white tracking-tight">AI Semantic Segmentation</span>
        </div>
        <div className="space-y-1 text-[10px] text-[#93a9c7]">
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Semantic Classification</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Semantic Labels (8 classes)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Confidence Scoring</span>
          </div>
        </div>
        <div className="mt-1.5 pt-1 border-t border-[#142642] flex justify-between items-center text-[9px] font-mono">
          <span className="text-[#5d7d9f]">Model:</span>
          <span className="text-cyan-400 font-bold">RandLA-Net</span>
        </div>
      </div>

      {/* Down Arrow 2 */}
      <div className="flex justify-center -my-1 text-[#3b82f6]">
        <ArrowDown className="w-3.5 h-3.5 animate-bounce" />
      </div>

      {/* 3. Adaptive Grid + 2.5D Mapping */}
      <div className="bg-[#071123] border border-[#162744] rounded-lg p-2 flex flex-col gap-1.5">
        <div className="flex items-center gap-1.5 mb-0.5">
          <div className="w-4 h-4 rounded bg-[#132c54] flex items-center justify-center text-[#38bdf8]">
            <Layers className="w-3 h-3" />
          </div>
          <span className="text-[11px] font-bold text-white tracking-tight">Adaptive Grid + 2.5D Mapping</span>
        </div>
        <div className="space-y-0.5 text-[9.5px] text-[#93a9c7]">
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Variable Resolution</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Elevation Map</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-cyan-400 font-bold">✓</span>
            <span>Semantic Layers</span>
          </div>
        </div>

        {/* Controls */}
        <div className="space-y-1.5 pt-1.5 border-t border-[#142642] text-[9px] font-mono text-[#7e9bbd]">
          {/* Base Res */}
          <div>
            <div className="flex justify-between">
              <span>Base Res:</span>
              <span className="text-white font-bold">{baseResolution.toFixed(2)} m</span>
            </div>
            <input
              type="range"
              min="0.50"
              max="2.00"
              step="0.10"
              value={baseResolution}
              onChange={(e) => onChangeBaseRes && onChangeBaseRes(parseFloat(e.target.value))}
              className="w-full h-1 bg-[#162744] rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>

          {/* Fine Res */}
          <div>
            <div className="flex justify-between">
              <span>Fine Res:</span>
              <span className="text-white font-bold">{fineResolution.toFixed(2)} m</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.50"
              step="0.05"
              value={fineResolution}
              onChange={(e) => onChangeFineRes && onChangeFineRes(parseFloat(e.target.value))}
              className="w-full h-1 bg-[#162744] rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>

          {/* Threshold */}
          <div>
            <div className="flex justify-between">
              <span>Importance Thresh:</span>
              <span className="text-white font-bold">{importanceThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.90"
              step="0.05"
              value={importanceThreshold}
              onChange={(e) => onChangeThreshold && onChangeThreshold(parseFloat(e.target.value))}
              className="w-full h-1 bg-[#162744] rounded-lg appearance-none cursor-pointer accent-cyan-400"
            />
          </div>
        </div>

        {/* Update 2.5D Adaptive Map Button */}
        <button
          onClick={onUpdateAdaptiveMap}
          disabled={isUpdatingMap}
          className="w-full mt-1 py-1 px-2 rounded bg-gradient-to-r from-[#1d4ed8] to-[#0284c7] hover:from-[#2563eb] hover:to-[#0ea5e9] text-white font-bold text-[9.5px] uppercase tracking-wider shadow-md shadow-blue-900/30 transition active:scale-95 disabled:opacity-50"
        >
          {isUpdatingMap ? 'UPDATING MAP...' : 'UPDATE 2.5D ADAPTIVE MAP'}
        </button>
      </div>
    </div>
  );
}
