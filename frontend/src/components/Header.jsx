import React from 'react';
import { Play, Pause, RotateCcw, ChevronLeft, ChevronRight, Server } from 'lucide-react';
import { SIMULATION_FRAMES } from '../config/constants';

export default function Header({
  selectedFrame,
  onSelectFrame,
  isPlaying,
  onTogglePlay,
  onReset,
  dataSource,
  onToggleDataSource,
  backendOnline,
  pingMs,
}) {
  const currentFrameMeta = SIMULATION_FRAMES.find((f) => f.id === selectedFrame) || SIMULATION_FRAMES[0];

  const handlePrevFrame = () => {
    const idx = SIMULATION_FRAMES.findIndex((f) => f.id === selectedFrame);
    const prevIdx = (idx - 1 + SIMULATION_FRAMES.length) % SIMULATION_FRAMES.length;
    onSelectFrame(SIMULATION_FRAMES[prevIdx].id);
  };

  const handleNextFrame = () => {
    const idx = SIMULATION_FRAMES.findIndex((f) => f.id === selectedFrame);
    const nextIdx = (idx + 1) % SIMULATION_FRAMES.length;
    onSelectFrame(SIMULATION_FRAMES[nextIdx].id);
  };

  return (
    <header className="bg-[#09101f] border-b border-[#172742] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 shadow-lg select-none">
      {/* Title & Brand matching reference */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-[#00d4ff]/10 border border-[#00d4ff]/40 flex items-center justify-center text-[#00d4ff] shadow-[0_0_12px_rgba(0,212,255,0.25)]">
          {/* Autonomous Vehicle Sensor Icon */}
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.5 2.8C2.1 10.7 2 10.8 2 11v5c0 .6.4 1 1 1h2" />
            <circle cx="7" cy="17" r="2" />
            <path d="M9 17h6" />
            <circle cx="17" cy="17" r="2" />
            <path d="M9 17h6" />
            <path d="M12 2v3M9 3.5a5 5 0 0 1 6 0" />
          </svg>
        </div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            Semantic 2.5D Elevation Map
          </h1>
          <p className="text-xs text-[#00d4ff] font-medium tracking-wide">
            LiDAR Perception + Adaptive Grid + Semantic Understanding
          </p>
        </div>
      </div>

      {/* Middle Interactive Playback & Dataset Controls */}
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 bg-[#050913] px-2 sm:px-3 py-1.5 rounded-md border border-[#172742]">
        <button
          onClick={onTogglePlay}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition ${
            isPlaying
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
              : 'bg-[#2563eb]/20 text-[#38bdf8] border border-[#2563eb]/50 hover:bg-[#2563eb]/30'
          }`}
          title={isPlaying ? 'Pause Playback' : 'Start Continuous Perception Simulation'}
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
          <span>{isPlaying ? 'Pause' : 'Play'}</span>
        </button>

        <div className="flex items-center">
          <button
            onClick={handlePrevFrame}
            className="p-1 rounded text-[#94a3b8] hover:text-white hover:bg-[#172742] transition"
            title="Previous Frame"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleNextFrame}
            className="p-1 rounded text-[#94a3b8] hover:text-white hover:bg-[#172742] transition"
            title="Next Frame"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <button
          onClick={onReset}
          className="p-1 rounded text-[#94a3b8] hover:text-white hover:bg-[#172742] transition"
          title="Reset View and Frame"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        <div className="h-4 w-[1px] bg-[#172742]" />

        {/* Frame Selector */}
        <div className="flex items-center gap-1.5 text-xs text-[#94a3b8]">
          <span className="font-semibold text-white">Select:</span>
          <select
            value={selectedFrame}
            onChange={(e) => onSelectFrame(e.target.value)}
            className="bg-[#0d172a] text-xs text-[#38bdf8] font-mono font-bold border border-[#1e3a5f] rounded px-2 py-0.5 outline-none cursor-pointer hover:border-[#00d4ff]"
          >
            {SIMULATION_FRAMES.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
        </div>

        <div className="h-4 w-[1px] bg-[#172742]" />

        {/* Data Source Toggle */}
        <button
          onClick={onToggleDataSource}
          className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold transition border ${
            dataSource === 'FastAPI'
              ? backendOnline
                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
              : 'bg-cyan-500/15 text-[#38bdf8] border-cyan-500/30'
          }`}
          title="Switch between Simulation and Live FastAPI Backend"
        >
          <Server className="w-3 h-3" />
          <span>{dataSource === 'FastAPI' ? (backendOnline ? `FastAPI (${pingMs || 12}ms)` : 'FastAPI (Offline)') : 'Simulation'}</span>
        </button>
      </div>

      {/* Right Status Badges matching reference screenshot: Real-time Processing, Dataset, Frame, Time */}
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 text-xs">
        {/* 1. Real-time Processing Pill */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Real-time Processing</span>
        </div>

        {/* 2. Dataset Pill */}
        <div className="flex items-center gap-1 text-[#94a3b8] bg-[#0d172a] border border-[#172742] px-2.5 py-1 rounded text-[11px]">
          <span>Dataset:</span>
          <span className="text-white font-medium">{currentFrameMeta.dataset}</span>
        </div>

        {/* 3. Frame Pill */}
        <div className="flex items-center gap-1 text-[#94a3b8] bg-[#0d172a] border border-[#172742] px-2.5 py-1 rounded text-[11px] font-mono">
          <span>Frame:</span>
          <span className="text-white font-bold">{selectedFrame}</span>
        </div>

        {/* 4. Time Pill */}
        <div className="flex items-center gap-1 text-[#94a3b8] bg-[#0d172a] border border-[#172742] px-2.5 py-1 rounded text-[11px] font-mono">
          <span>Time:</span>
          <span className="text-white font-bold">{currentFrameMeta.time}</span>
        </div>
      </div>
    </header>
  );
}
