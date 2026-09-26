/**
 * Header.jsx
 * Top navigation header strictly aligned with reference layout:
 * - Left: Hexagon Box Logo, Title, Subtitle
 * - Right: Dataset, Sequence, Frame Stepper with Play/Pause, Speed, Reset View, Export, Status, and Timestamp.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  SkipBack,
  RotateCcw,
  Download,
} from 'lucide-react';

export default function Header({
  frameId = '000000',
  availableFrames = [],
  onSelectFrame,
  statusText = 'Processing Complete',
  backendConnected = true,
  onStepNext,
  onStepPrev,
  onStepFirst,
  onTogglePlay,
  isPlaying = false,
  playbackSpeed = 1,
  onChangeSpeed,
  onResetView,
  onExport,
}) {
  const [selectedDataset, setSelectedDataset] = useState('SemanticKITTI');
  const [selectedSequence, setSelectedSequence] = useState('00');
  const [currentTimeStr, setCurrentTimeStr] = useState('Sep 26, 2026 21:45:00');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const month = monthNames[now.getMonth()];
      const day = now.getDate();
      const year = now.getFullYear();
      const time = now.toTimeString().split(' ')[0];
      setCurrentTimeStr(`${month} ${day}, ${year} ${time}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 bg-[#060c18] border-b border-[#14233c] px-4 md:px-5 flex items-center justify-between z-30 select-none shrink-0 text-xs">
      {/* 1. Left Branding */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="w-8 h-8 rounded-lg bg-[#1e40af] border border-[#3b82f6] flex items-center justify-center shadow-md shadow-blue-500/20">
          <Box className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="text-[15px] font-bold tracking-tight text-white flex items-center gap-2">
            LiDAR Adaptive 2.5D Mapping System
          </h1>
          <p className="text-[11px] text-[#7892b4] font-medium tracking-wide">
            Semantic Understanding &nbsp;|&nbsp; Adaptive Grid &nbsp;|&nbsp; Efficient Perception
          </p>
        </div>
      </div>

      {/* 1. Right Dataset / Sequence / Frame Controls / Status / Time */}
      <div className="flex items-center gap-2 md:gap-2.5 font-mono text-[11px]">
        {/* Dataset */}
        <div className="hidden lg:flex items-center gap-1">
          <span className="text-[#6484ae] text-[10px] font-sans">Dataset:</span>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            className="bg-[#0a1428] border border-[#1a3258] text-white rounded px-1.5 py-0.5 focus:outline-none focus:border-blue-500 text-[10.5px]"
          >
            <option value="SemanticKITTI">SemanticKITTI</option>
            <option value="nuScenes">nuScenes</option>
            <option value="Waymo">Waymo</option>
          </select>
        </div>

        {/* Sequence */}
        <div className="hidden md:flex items-center gap-1">
          <span className="text-[#6484ae] text-[10px] font-sans">Sequence:</span>
          <select
            value={selectedSequence}
            onChange={(e) => setSelectedSequence(e.target.value)}
            className="bg-[#0a1428] border border-[#1a3258] text-white rounded px-1.5 py-0.5 focus:outline-none focus:border-blue-500 text-[10.5px]"
          >
            <option value="00">00</option>
            <option value="01">01</option>
            <option value="02">02</option>
          </select>
        </div>

        {/* Frame Stepper + Playback Buttons */}
        <div className="flex items-center gap-1 bg-[#0a1428] border border-[#1a3258] px-1.5 py-0.5 rounded-md">
          <span className="text-[#6484ae] text-[10px] font-sans mr-0.5">Frame:</span>
          <select
            value={frameId}
            onChange={(e) => onSelectFrame && onSelectFrame(e.target.value)}
            className="bg-transparent text-white text-[11px] rounded focus:outline-none font-mono cursor-pointer"
          >
            {availableFrames && availableFrames.length > 0 ? (
              availableFrames.map((f) => {
                const id = f.frame_id || f.id || f;
                return (
                  <option key={id} value={id} className="bg-[#0a1428] text-white">
                    {id}
                  </option>
                );
              })
            ) : (
              <option value={frameId}>{frameId}</option>
            )}
          </select>

          {/* Stepper & Play/Pause Controls */}
          <div className="flex items-center gap-0.5 ml-1 border-l border-[#1a3258] pl-1">
            {onStepFirst && (
              <button
                onClick={onStepFirst}
                className="p-1 rounded text-[#8da8cf] hover:text-white hover:bg-[#14233c] transition"
                title="First Frame"
              >
                <SkipBack className="w-3 h-3" />
              </button>
            )}
            <button
              onClick={onStepPrev}
              className="p-1 rounded text-[#8da8cf] hover:text-white hover:bg-[#14233c] transition"
              title="Previous Frame"
            >
              <ChevronLeft className="w-3 h-3" />
            </button>

            {/* Main Play / Pause Button */}
            <button
              onClick={onTogglePlay}
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 transition ${
                isPlaying
                  ? 'bg-amber-600 text-white shadow-sm shadow-amber-500/30'
                  : 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/30'
              }`}
              title={isPlaying ? 'Pause Simulation' : 'Play Live Driving Simulation'}
            >
              {isPlaying ? (
                <>
                  <Pause className="w-2.5 h-2.5 fill-current" />
                  <span className="hidden sm:inline">Pause</span>
                </>
              ) : (
                <>
                  <Play className="w-2.5 h-2.5 fill-current" />
                  <span className="hidden sm:inline">Play</span>
                </>
              )}
            </button>

            <button
              onClick={onStepNext}
              className="p-1 rounded text-[#8da8cf] hover:text-white hover:bg-[#14233c] transition"
              title="Next Frame"
            >
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>

          {/* Playback Speed Toggles */}
          {onChangeSpeed && (
            <div className="hidden sm:flex items-center gap-0.5 border-l border-[#1a3258] pl-1 text-[9.5px]">
              {[1, 2, 4].map((spd) => (
                <button
                  key={spd}
                  onClick={() => onChangeSpeed(spd)}
                  className={`px-1 py-0.2 rounded font-mono ${
                    playbackSpeed === spd
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-[#6484ae] hover:text-white'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Reset View Button */}
        {onResetView && (
          <button
            onClick={onResetView}
            className="flex items-center gap-1 px-1.5 py-1 rounded bg-[#0a1428] border border-[#1a3258] hover:border-[#38bdf8] text-[#8da8cf] hover:text-white transition text-[10.5px]"
            title="Reset 3D Camera View"
          >
            <RotateCcw className="w-3 h-3 text-cyan-400" />
            <span className="hidden xl:inline">Reset</span>
          </button>
        )}

        {/* Export Button */}
        {onExport && (
          <button
            onClick={onExport}
            className="flex items-center gap-1 px-1.5 py-1 rounded bg-[#0a1428] border border-[#1a3258] hover:border-[#38bdf8] text-[#8da8cf] hover:text-white transition text-[10.5px]"
            title="Export 2.5D Map JSON Data"
          >
            <Download className="w-3 h-3 text-blue-400" />
            <span className="hidden xl:inline">Export</span>
          </button>
        )}

        {/* Status Indicator */}
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#062419] border border-[#107044] text-[#1fe88b] text-[10.5px] font-sans font-semibold shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-[#1fe88b] animate-pulse" />
          <span>{statusText || 'Processing Complete'}</span>
        </div>

        {/* Timestamp */}
        <span className="hidden 2xl:inline text-[#718eb3] text-[10.5px] shrink-0">
          {currentTimeStr}
        </span>
      </div>
    </header>
  );
}
