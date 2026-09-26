/**
 * Header.jsx
 * Top navigation header matching reference dashboard.
 */

import React from 'react';
import { Car, RefreshCw, Download, CheckCircle2 } from 'lucide-react';

export default function Header({
  frameId = '000000',
  availableFrames = [],
  onSelectFrame,
  isLive = true,
  statusText = 'ANALYSIS READY',
  backendConnected = true,
  onResetView,
  onExport,
  onStepNext,
  onStepPrev,
  onTogglePlay,
  isPlaying = false,
  playbackSpeed = 1,
  onChangeSpeed,
}) {
  return (
    <header className="min-h-14 bg-[#050b18] border-b border-[#14233c] px-3 md:px-4 py-2 md:py-0 flex flex-col md:flex-row items-center justify-between z-30 select-none shrink-0 gap-2 md:gap-0">
      {/* Left Branding */}
      <div className="flex items-center gap-2 md:gap-3 shrink-0">
        <div className="w-8 h-8 md:w-9 md:h-9 rounded-lg bg-[#0e3b78] border border-[#1d5fb5] flex items-center justify-center shadow-lg shadow-blue-500/10">
          <Car className="w-4 h-4 md:w-5 md:h-5 text-white" />
        </div>
        <div>
          <h1 className="text-[11px] md:text-sm font-bold tracking-tight text-white flex items-center gap-2">
            ADAPTIVE 2.5D LiDAR PERCEPTION
          </h1>
          <p className="hidden sm:block text-[11px] text-[#7892b4] font-medium">
            Dynamic Environment Mapping &amp; Variable-Resolution Grid Pipeline
          </p>
        </div>
      </div>

      {/* Right Status & Controls */}
      <div className="flex flex-wrap items-center gap-2 md:gap-3 text-xs font-mono w-full md:w-auto">
        {/* Backend Connected / Status Badge */}
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-semibold ${
          backendConnected
            ? 'bg-[#072418] border-[#107044] text-[#1fe88b]'
            : 'bg-[#260f12] border-[#7f1d1d] text-[#f87171]'
        }`}>
          <span className={`w-2 h-2 rounded-full ${backendConnected ? 'bg-[#1fe88b] animate-pulse' : 'bg-[#f87171]'}`} />
          <span>{statusText}</span>
        </div>

        {/* Reset View Button */}
        {onResetView && (
          <button
            onClick={onResetView}
            className="flex items-center gap-1 px-2 py-1 rounded bg-[#09152b] border border-[#1a3258] hover:border-[#38bdf8] text-[#94a8c9] hover:text-white transition text-[11px]"
            title="Reset 3D Camera View"
          >
            <RefreshCw className="w-3 h-3" />
            <span className="hidden sm:inline">Reset View</span>
          </button>
        )}

        {/* Export Button */}
        {onExport && (
          <button
            onClick={onExport}
            className="flex items-center gap-1 px-2 py-1 rounded bg-[#09152b] border border-[#1a3258] hover:border-[#38bdf8] text-[#94a8c9] hover:text-white transition text-[11px]"
            title="Export 2.5D Map Data"
          >
            <Download className="w-3 h-3" />
            <span className="hidden sm:inline">Export</span>
          </button>
        )}

        {/* Current Frame Selector & Step Controls */}
        <div className="flex items-center gap-2 bg-[#09152b] border border-[#1a3258] px-2.5 py-1 rounded-md">
          <span className="text-[#597499]">Frame:</span>
          {availableFrames && availableFrames.length > 0 ? (
            <select
              value={frameId}
              onChange={(e) => onSelectFrame && onSelectFrame(e.target.value)}
              className="bg-transparent text-white font-bold font-mono text-xs focus:outline-none cursor-pointer"
            >
              {availableFrames.map((f) => (
                <option key={f.frame_id || f.id} value={f.frame_id || f.id} className="bg-[#09152b] text-white">
                  {f.frame_id || f.id}
                </option>
              ))}
            </select>
          ) : (
            <span className="text-white font-bold">{frameId}</span>
          )}

          {/* Stepper Buttons */}
          <div className="flex items-center gap-1 ml-1 border-l border-[#1a3258] pl-2">
            <button
              onClick={onStepPrev}
              className="text-[#7892b4] hover:text-white px-1 text-[11px]"
              title="Previous Frame"
            >
              ◀
            </button>
            <button
              onClick={onTogglePlay}
              className="text-cyan-400 hover:text-cyan-300 px-1 text-[11px] font-bold"
              title={isPlaying ? 'Pause Playback' : 'Play Sequence'}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
            <button
              onClick={onStepNext}
              className="text-[#7892b4] hover:text-white px-1 text-[11px]"
              title="Next Frame"
            >
              ▶
            </button>
          </div>

          {/* Speed Selector */}
          {onChangeSpeed && (
            <div className="flex items-center gap-0.5 border-l border-[#1a3258] pl-2">
              {[1, 2, 4].map((spd) => (
                <button
                  key={spd}
                  onClick={() => onChangeSpeed(spd)}
                  className={`px-1 py-0.5 text-[10px] rounded ${
                    playbackSpeed === spd
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-[#597499] hover:text-white'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
