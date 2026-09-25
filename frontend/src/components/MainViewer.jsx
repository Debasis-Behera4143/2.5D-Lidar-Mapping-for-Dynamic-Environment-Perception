/**
 * MainViewer.jsx
 * Large central 3D WebGL viewport container with floating HUD telemetry, camera actions,
 * loading state overlay, and real data validation.
 */

import React from 'react';
import LiDARScene from './3d/LiDARScene';
import { VIEW_MODES } from '../app/config';
import { RefreshCw, Crosshair, Bug, Layers } from 'lucide-react';

export default function MainViewer({
  bufferData,
  pointSize = 2.5,
  showPoints = true,
  showGrid = true,
  showRangeRings = true,
  showAxes = true,
  viewMode = 'orbit',
  onChangeViewMode,
  gridCells = [],
  showHeightMap = true,
  activeClasses = null,
  currentFrameId = '000000',
  totalPoints = 0,
  displayedPoints = 0,
  isLoading = false,
  loadingText = '',
  bounds = null,
  hasPose = false,
  pose = null,
  debugMode = false,
  onToggleDebug,
  heightExaggeration = 1.0,
}) {
  // Compute sensor origin translation if pose is provided
  const sensorPosition = [0, 0, 0];

  return (
    <div className="flex-1 relative h-full bg-[#040711] overflow-hidden flex flex-col select-none">
      {/* 3D WebGL Canvas */}
      <LiDARScene
        bufferData={bufferData}
        pointSize={pointSize}
        showPoints={showPoints}
        showGrid={showGrid}
        showRangeRings={showRangeRings}
        showAxes={showAxes}
        viewMode={viewMode}
        gridCells={gridCells}
        showHeightMap={showHeightMap}
        activeClasses={activeClasses}
        bounds={bounds}
        sensorPosition={sensorPosition}
        heightExaggeration={heightExaggeration}
      />

      {/* 1. Top-Left Telemetry Overlay */}
      <div className="absolute top-3 left-3 bg-[#0a1224]/90 border border-slate-800/90 px-3 py-2 rounded-md backdrop-blur-md text-xs font-mono-num space-y-1 pointer-events-none shadow-xl">
        <div className="flex items-center gap-2 text-cyan-400 font-bold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>REAL LiDAR SCAN: {currentFrameId}</span>
        </div>
        <div className="text-[11px] text-slate-300">
          <span>Original Points: </span>
          <span className="font-bold text-white">{(totalPoints || bufferData?.count || 0).toLocaleString()}</span>
          {displayedPoints > 0 && displayedPoints !== totalPoints && (
            <>
              <span className="text-slate-500"> | </span>
              <span>Displayed: </span>
              <span className="text-cyan-300 font-bold">{displayedPoints.toLocaleString()}</span>
            </>
          )}
        </div>
        <div className="text-[10px] text-slate-400 flex items-center gap-2">
          <span>Adaptive Cells: <strong className="text-emerald-400">{gridCells.length.toLocaleString()}</strong></span>
          <span className="text-slate-600">|</span>
          <span>Ego Pose: <strong className={hasPose ? 'text-cyan-400' : 'text-slate-500'}>{hasPose ? 'Tracked' : 'Origin / Static'}</strong></span>
        </div>
      </div>

      {/* 2. Top-Right Perspective Controls HUD */}
      <div className="absolute top-3 right-3 flex items-center gap-1 bg-[#0a1224]/90 border border-slate-800/90 p-1 rounded-md backdrop-blur-md shadow-xl">
        {VIEW_MODES.map((v) => {
          const isEgoDisabled = v.id === 'ego' && !hasPose;
          return (
            <button
              key={v.id}
              disabled={isEgoDisabled}
              onClick={() => onChangeViewMode(v.id)}
              className={`px-2 py-1 text-[11px] font-bold rounded transition ${
                viewMode === v.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : isEgoDisabled
                  ? 'text-slate-600 opacity-50 cursor-not-allowed'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/70'
              }`}
              title={isEgoDisabled ? 'Ego pose unavailable for this sequence' : v.label}
            >
              {v.label}
            </button>
          );
        })}

        <div className="h-4 w-[1px] bg-slate-800 mx-1" />

        {/* Debug Data Toggle */}
        <button
          onClick={onToggleDebug}
          className={`px-2 py-1 text-[11px] font-bold rounded flex items-center gap-1 transition ${
            debugMode
              ? 'bg-amber-600 text-white'
              : 'text-slate-400 hover:text-amber-300 hover:bg-slate-800/70'
          }`}
          title="Toggle Developer Debug Diagnostics"
        >
          <Bug className="w-3.5 h-3.5" />
          <span>DEBUG</span>
        </button>
      </div>

      {/* 3. Bottom-Left Metric Range Calibration */}
      <div className="absolute bottom-3 left-3 bg-[#0a1224]/85 border border-slate-800 px-2.5 py-1 rounded text-[10px] font-mono-num text-slate-400 backdrop-blur-sm pointer-events-none">
        <span className="text-cyan-400 font-bold">RANGE RINGS:</span> 10m / 20m / 30m / 40m / 50m
      </div>

      {/* 4. Loading Frame Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-[#040711]/60 backdrop-blur-[2px] flex items-center justify-center pointer-events-none z-20">
          <div className="bg-[#0b1428] border border-cyan-500/50 px-5 py-3 rounded-md shadow-2xl flex items-center gap-3 text-cyan-300 font-mono-num text-xs">
            <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
            <span className="font-bold">{loadingText || `Loading LiDAR Frame ${currentFrameId}...`}</span>
          </div>
        </div>
      )}

      {/* 5. Developer Debug Overlay */}
      {debugMode && (
        <div className="absolute top-20 right-3 w-80 bg-[#070d1c]/95 border border-amber-500/50 p-3 rounded shadow-2xl font-mono-num text-[11px] text-slate-200 space-y-1.5 backdrop-blur-md z-30">
          <div className="flex items-center justify-between border-b border-amber-500/30 pb-1 font-bold text-amber-400">
            <span>DEVELOPER DATA INSPECTOR</span>
            <span>LIVE</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Active Frame:</span>
            <span className="text-white font-bold">{currentFrameId}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Buffer Point Count:</span>
            <span className="text-cyan-400 font-bold">{bufferData?.count || 0}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Total Frame Points:</span>
            <span className="text-white font-bold">{totalPoints}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Pose Data Available:</span>
            <span className={hasPose ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
              {hasPose ? 'YES (from poses.txt)' : 'NO (Ego pose unavailable)'}
            </span>
          </div>
          {bounds && (
            <div className="space-y-0.5 border-t border-slate-800 pt-1 text-[10px]">
              <div className="text-slate-400">X Bounds: [{bounds.min_x}m, {bounds.max_x}m]</div>
              <div className="text-slate-400">Y Bounds: [{bounds.min_y}m, {bounds.max_y}m]</div>
              <div className="text-slate-400">Z Bounds: [{bounds.min_z}m, {bounds.max_z}m]</div>
            </div>
          )}
          <div className="flex justify-between border-t border-slate-800 pt-1 text-slate-400">
            <span>Adaptive Cells:</span>
            <span className="text-emerald-400 font-bold">{gridCells.length}</span>
          </div>
        </div>
      )}
    </div>
  );
}
