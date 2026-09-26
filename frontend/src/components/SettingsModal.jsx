/**
 * SettingsModal.jsx
 * Executive-grade System Settings & Calibration Modal.
 * Allows live configuration of:
 * - 2.5D Adaptive Grid parameters (base res, fine res, importance threshold)
 * - ADAS Collision Avoidance & Path Planning settings
 * - 3D Point Cloud graphics & visualization settings
 * - Backend service connection & hardware diagnostics
 */

import React, { useState, useEffect } from 'react';
import {
  Settings,
  X,
  Cpu,
  Sliders,
  Shield,
  Eye,
  Check,
  RotateCcw,
  Zap,
} from 'lucide-react';

export default function SettingsModal({
  isOpen = false,
  onClose,
  baseResolution = 1.0,
  fineResolution = 0.25,
  importanceThreshold = 0.50,
  onChangeBaseResolution,
  onChangeFineResolution,
  onChangeImportanceThreshold,
  pointSize = 0.07,
  onChangePointSize,
  onApplySettings,
}) {
  const [localBaseRes, setLocalBaseRes] = useState(baseResolution);
  const [localFineRes, setLocalFineRes] = useState(fineResolution);
  const [localThreshold, setLocalThreshold] = useState(importanceThreshold);
  const [localPointSize, setLocalPointSize] = useState(pointSize);
  const [targetFps, setTargetFps] = useState('60');
  const [avoidanceBuffer, setAvoidanceBuffer] = useState('2.4');
  const [shadowsEnabled, setShadowsEnabled] = useState(true);
  const [radarWavesEnabled, setRadarWavesEnabled] = useState(true);
  const [activeTab, setActiveTab] = useState('grid'); // 'grid' | 'adas' | 'graphics' | 'backend'

  useEffect(() => {
    setLocalBaseRes(baseResolution);
    setLocalFineRes(fineResolution);
    setLocalThreshold(importanceThreshold);
    setLocalPointSize(pointSize);
  }, [baseResolution, fineResolution, importanceThreshold, pointSize, isOpen]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose && onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSaveAndApply = () => {
    if (onChangeBaseResolution) onChangeBaseResolution(localBaseRes);
    if (onChangeFineResolution) onChangeFineResolution(localFineRes);
    if (onChangeImportanceThreshold) onChangeImportanceThreshold(localThreshold);
    if (onChangePointSize) onChangePointSize(localPointSize);
    if (onApplySettings) {
      onApplySettings({
        baseResolution: localBaseRes,
        fineResolution: localFineRes,
        importanceThreshold: localThreshold,
        pointSize: localPointSize,
        targetFps,
        avoidanceBuffer,
        shadowsEnabled,
        radarWavesEnabled,
      });
    }
    onClose && onClose();
  };

  const handleResetDefaults = () => {
    setLocalBaseRes(1.0);
    setLocalFineRes(0.25);
    setLocalThreshold(0.50);
    setLocalPointSize(0.07);
    setTargetFps('60');
    setAvoidanceBuffer('2.4');
    setShadowsEnabled(true);
    setRadarWavesEnabled(true);
  };

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      {/* Modal Dialog Card */}
      <div className="w-full max-w-2xl bg-[#060c18] border border-[#1a3258] rounded-xl shadow-2xl shadow-blue-950/60 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-5 py-3.5 bg-[#081224] border-b border-[#14233c] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
              <Settings className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight">System Settings & Calibration</h2>
              <p className="text-[11px] text-[#718eb3]">Configure perception pipeline, ADAS parameters, and GPU rendering</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-md text-[#8da8cf] hover:text-white hover:bg-[#14233c] transition cursor-pointer"
            title="Close (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 px-5 pt-3 border-b border-[#14233c] text-xs font-medium">
          <button
            onClick={() => setActiveTab('grid')}
            className={`pb-2 px-2.5 border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'grid'
                ? 'border-blue-500 text-white font-bold'
                : 'border-transparent text-[#718eb3] hover:text-slate-300'
            }`}
          >
            <Sliders className="w-3.5 h-3.5 text-blue-400" />
            <span>2.5D Grid Partition</span>
          </button>

          <button
            onClick={() => setActiveTab('adas')}
            className={`pb-2 px-2.5 border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'adas'
                ? 'border-blue-500 text-white font-bold'
                : 'border-transparent text-[#718eb3] hover:text-slate-300'
            }`}
          >
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>ADAS Collision Avoidance</span>
          </button>

          <button
            onClick={() => setActiveTab('graphics')}
            className={`pb-2 px-2.5 border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'graphics'
                ? 'border-blue-500 text-white font-bold'
                : 'border-transparent text-[#718eb3] hover:text-slate-300'
            }`}
          >
            <Eye className="w-3.5 h-3.5 text-cyan-400" />
            <span>3D Graphics & POV</span>
          </button>

          <button
            onClick={() => setActiveTab('backend')}
            className={`pb-2 px-2.5 border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'backend'
                ? 'border-blue-500 text-white font-bold'
                : 'border-transparent text-[#718eb3] hover:text-slate-300'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
            <span>Backend & Hardware</span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-5 flex-1 overflow-y-auto space-y-4 text-xs font-sans text-slate-200">
          {/* TAB 1: 2.5D GRID PARTITION */}
          {activeTab === 'grid' && (
            <div className="space-y-4">
              <div className="bg-[#091428] border border-[#1a3258] rounded-lg p-3 space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-white">Coarse Base Resolution (r_base)</span>
                    <span className="font-mono text-cyan-400 font-bold">{localBaseRes.toFixed(2)} m</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.05"
                    value={localBaseRes}
                    onChange={(e) => setLocalBaseRes(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[#14233c] rounded appearance-none cursor-pointer accent-blue-500"
                  />
                  <p className="text-[10.5px] text-[#718eb3] mt-1">
                    Used for static background regions (road surfaces, walls, buildings) to maximize memory savings.
                  </p>
                </div>

                <div className="border-t border-[#14233c] pt-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-white">Fine Grid Resolution (r_fine)</span>
                    <span className="font-mono text-cyan-400 font-bold">{localFineRes.toFixed(2)} m</span>
                  </div>
                  <input
                    type="range"
                    min="0.10"
                    max="0.50"
                    step="0.05"
                    value={localFineRes}
                    onChange={(e) => setLocalFineRes(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[#14233c] rounded appearance-none cursor-pointer accent-blue-500"
                  />
                  <p className="text-[10.5px] text-[#718eb3] mt-1">
                    High-density elevation partition for dynamic obstacles (vehicles, pedestrians, curbs).
                  </p>
                </div>

                <div className="border-t border-[#14233c] pt-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-white">Dynamic Importance Threshold (tau_imp)</span>
                    <span className="font-mono text-cyan-400 font-bold">{localThreshold.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.20"
                    max="0.80"
                    step="0.05"
                    value={localThreshold}
                    onChange={(e) => setLocalThreshold(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[#14233c] rounded appearance-none cursor-pointer accent-blue-500"
                  />
                  <p className="text-[10.5px] text-[#718eb3] mt-1">
                    Threshold triggering fine-cell sub-division for critical safety areas.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ADAS COLLISION AVOIDANCE */}
          {activeTab === 'adas' && (
            <div className="space-y-3">
              <div className="bg-[#091428] border border-[#1a3258] rounded-lg p-3 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white block">Autonomous Overtaking Clearance</span>
                    <p className="text-[10.5px] text-[#718eb3]">Lateral distance maintained while overtaking obstacles</p>
                  </div>
                  <select
                    value={avoidanceBuffer}
                    onChange={(e) => setAvoidanceBuffer(e.target.value)}
                    className="bg-[#0a1428] border border-[#1a3258] text-white text-xs rounded px-2 py-1 font-mono"
                  >
                    <option value="2.0">2.0 m (Standard)</option>
                    <option value="2.4">2.4 m (Recommended Wide)</option>
                    <option value="2.8">2.8 m (Maximum Margin)</option>
                  </select>
                </div>

                <div className="border-t border-[#14233c] pt-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white block">Trajectory Guidance Path Markers</span>
                    <p className="text-[10.5px] text-[#718eb3]">Render glowing S-curve avoidance path on road surface</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={radarWavesEnabled}
                    onChange={(e) => setRadarWavesEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-blue-600 bg-[#0a1428] border-[#1a3258] cursor-pointer"
                  />
                </div>

                <div className="border-t border-[#14233c] pt-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white block">Active Collision Prevention Alert</span>
                    <p className="text-[10.5px] text-[#718eb3]">Show 3D HUD reticles and distance badges on tracked cars</p>
                  </div>
                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-500/40 px-2 py-0.5 rounded">
                    ACTIVE (SAFE)
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: 3D GRAPHICS */}
          {activeTab === 'graphics' && (
            <div className="space-y-3">
              <div className="bg-[#091428] border border-[#1a3258] rounded-lg p-3 space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-white">LiDAR Point Rendering Size</span>
                    <span className="font-mono text-cyan-400 font-bold">{localPointSize.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.03"
                    max="0.18"
                    step="0.01"
                    value={localPointSize}
                    onChange={(e) => setLocalPointSize(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-[#14233c] rounded appearance-none cursor-pointer accent-blue-500"
                  />
                </div>

                <div className="border-t border-[#14233c] pt-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white block">Target FPS Ceiling</span>
                    <p className="text-[10.5px] text-[#718eb3]">Limits WebGL requestAnimationFrame loop</p>
                  </div>
                  <select
                    value={targetFps}
                    onChange={(e) => setTargetFps(e.target.value)}
                    className="bg-[#0a1428] border border-[#1a3258] text-white text-xs rounded px-2 py-1 font-mono"
                  >
                    <option value="30">30 FPS (Power Saver)</option>
                    <option value="60">60 FPS (Balanced)</option>
                    <option value="120">Uncapped (GPU Max)</option>
                  </select>
                </div>

                <div className="border-t border-[#14233c] pt-3 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-white block">Digital Twin Shading & Tone Mapping</span>
                    <p className="text-[10.5px] text-[#718eb3]">ACESFilmic tone mapping with metallic automotive shaders</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={shadowsEnabled}
                    onChange={(e) => setShadowsEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-blue-600 bg-[#0a1428] border-[#1a3258] cursor-pointer"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: BACKEND & HARDWARE */}
          {activeTab === 'backend' && (
            <div className="space-y-3 font-mono text-[11px]">
              <div className="bg-[#091428] border border-[#1a3258] rounded-lg p-3 space-y-2.5">
                <div className="flex justify-between items-center">
                  <span className="text-[#718eb3] font-sans">FastAPI Backend Status:</span>
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Online (Port 8000)
                  </span>
                </div>

                <div className="flex justify-between items-center border-t border-[#14233c] pt-2">
                  <span className="text-[#718eb3] font-sans">Perception Latency:</span>
                  <span className="text-white font-bold">55 ms (18.2 FPS)</span>
                </div>

                <div className="flex justify-between items-center border-t border-[#14233c] pt-2">
                  <span className="text-[#718eb3] font-sans">Active AI Backbone:</span>
                  <span className="text-cyan-400 font-bold font-sans">RandLA-Net · 8 Semantic Classes</span>
                </div>

                <div className="flex justify-between items-center border-t border-[#14233c] pt-2">
                  <span className="text-[#718eb3] font-sans">Acceleration Device:</span>
                  <span className="text-purple-400 font-bold">PyTorch CUDA / Multi-Thread CPU</span>
                </div>

                <div className="flex justify-between items-center border-t border-[#14233c] pt-2">
                  <span className="text-[#718eb3] font-sans">Data Source Sequence:</span>
                  <span className="text-amber-400 font-bold">SemanticKITTI Sequence 00</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 bg-[#081224] border-t border-[#14233c] flex items-center justify-between">
          <button
            onClick={handleResetDefaults}
            className="flex items-center gap-1 text-[11px] text-[#718eb3] hover:text-white transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset to Defaults</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-md bg-[#0a1428] border border-[#1a3258] text-[#8da8cf] hover:text-white transition text-xs font-medium cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveAndApply}
              className="px-4 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/20 transition flex items-center gap-1.5 cursor-pointer"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Apply Settings</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
