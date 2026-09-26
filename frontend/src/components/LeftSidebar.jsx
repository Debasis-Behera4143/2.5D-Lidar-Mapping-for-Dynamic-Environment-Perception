/**
 * LeftSidebar.jsx
 * Fully interactive Left Sidebar aligned with reference specifications:
 * - 2. Navigation Menu with real click handlers
 * - 3. Frame Controls with real Play/Pause, Stepper, and Load Frame
 * - 4. Visualization Options directly updating 3D scene layers
 * - 5. Map Type switcher (Uniform, Adaptive, Both)
 * - 6. Run Processing action button
 * Spacious layout with comfortable typography and button targets.
 */

import React, { useState } from 'react';
import {
  LayoutDashboard,
  Box,
  Layers,
  PieChart,
  Activity,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  Loader2,
} from 'lucide-react';

export default function LeftSidebar({
  currentFrameId = '000000',
  availableFrames = [],
  onSelectFrame,
  onStepPrev,
  onStepNext,
  onLoadFrame,
  isLoadingFrame = false,
  mapType = 'adaptive',
  onChangeMapType,
  onRunProcessing,
  isProcessing = false,
  showGrid = true,
  onToggleGrid,
  showBoundingBoxes = true,
  onToggleBoundingBoxes,
  showTrajectory = false,
  onToggleTrajectory,
  colorBy = 'Semantic Class',
  onChangeColorBy,
  isPlaying = false,
  onTogglePlay,
  onSelectNav,
  activeNav: propActiveNav = 'dashboard',
}) {
  const [localActiveNav, setLocalActiveNav] = useState('dashboard');
  const [selectedSequence, setSelectedSequence] = useState('00');

  const activeNav = propActiveNav || localActiveNav;

  const handleNavClick = (id) => {
    setLocalActiveNav(id);
    if (onSelectNav) onSelectNav(id);
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'pointcloud', label: 'Point Cloud Viewer', icon: Box },
    { id: 'mapping', label: '2.5D Mapping', icon: Layers },
    { id: 'semantic', label: 'Semantic Analysis', icon: PieChart },
    { id: 'performance', label: 'Performance', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'help', label: 'Help', icon: HelpCircle },
  ];

  return (
    <aside className="w-64 shrink-0 bg-[#060c18] border border-[#14233c] rounded-lg p-3 flex flex-col gap-3 select-none text-xs">
      {/* 2. Navigation Menu */}
      <div className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-[12.5px] font-medium transition cursor-pointer ${
                isActive
                  ? 'bg-[#1d4ed8] text-white shadow-md shadow-blue-500/30'
                  : 'text-[#8da8cf] hover:text-white hover:bg-[#0c1933]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#6484ae]'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="border-t border-[#14233c]" />

      {/* 3. Frame Controls */}
      <div className="space-y-2">
        <span className="text-xs font-bold text-white block">Frame Controls</span>
        
        <div className="flex items-center justify-between gap-2">
          <span className="text-[11px] text-[#718eb3]">Sequence</span>
          <select
            value={selectedSequence}
            onChange={(e) => setSelectedSequence(e.target.value)}
            className="w-24 bg-[#0a1428] border border-[#1a3258] text-white text-xs rounded px-2 py-1 focus:outline-none focus:border-blue-500 font-mono cursor-pointer"
          >
            <option value="00">00 (KITTI)</option>
            <option value="01">01</option>
            <option value="02">02</option>
          </select>
        </div>

        <div>
          <span className="text-[11px] text-[#718eb3] block mb-1">Frame</span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={onStepPrev}
              className="p-1.5 rounded bg-[#0a1428] border border-[#1a3258] text-[#8da8cf] hover:text-white hover:border-[#2b4c80] transition cursor-pointer"
              title="Previous Frame"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <select
              value={currentFrameId}
              onChange={(e) => onSelectFrame && onSelectFrame(e.target.value)}
              className="flex-1 bg-[#0a1428] border border-[#1a3258] text-white text-xs font-mono text-center rounded py-1 px-1 focus:outline-none focus:border-blue-500 cursor-pointer"
            >
              {availableFrames && availableFrames.length > 0 ? (
                availableFrames.map((f) => {
                  const id = f.frame_id || f.id || f;
                  return (
                    <option key={id} value={id}>
                      {id}
                    </option>
                  );
                })
              ) : (
                <option value={currentFrameId}>{currentFrameId}</option>
              )}
            </select>

            <button
              onClick={onStepNext}
              className="p-1.5 rounded bg-[#0a1428] border border-[#1a3258] text-[#8da8cf] hover:text-white hover:border-[#2b4c80] transition cursor-pointer"
              title="Next Frame"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Load Frame and Play/Pause Actions */}
        <div className="grid grid-cols-2 gap-1.5 pt-1">
          <button
            onClick={onLoadFrame}
            disabled={isLoadingFrame}
            className="flex items-center justify-center gap-1.5 py-1.5 rounded bg-[#1e40af] hover:bg-[#1d4ed8] text-white font-medium text-[11.5px] shadow transition disabled:opacity-50 cursor-pointer"
            title="Load selected frame into memory"
          >
            {isLoadingFrame ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <span>Load Frame</span>
            )}
          </button>

          <button
            onClick={onTogglePlay}
            className={`flex items-center justify-center gap-1.5 py-1.5 rounded text-white font-medium text-[11.5px] shadow transition cursor-pointer ${
              isPlaying
                ? 'bg-amber-600 hover:bg-amber-500'
                : 'bg-emerald-600 hover:bg-emerald-500'
            }`}
            title={isPlaying ? 'Pause car and frame playback' : 'Start car driving simulation'}
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Play Live</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className="border-t border-[#14233c]" />

      {/* 4. Visualization Options */}
      <div className="space-y-1.5">
        <span className="text-xs font-bold text-white block mb-1">Visualization Options</span>
        
        <label className="flex items-center gap-2 text-[#cbd5e1] hover:text-white cursor-pointer text-[11.5px]">
          <input
            type="checkbox"
            checked={showGrid}
            onChange={(e) => onToggleGrid && onToggleGrid(e.target.checked)}
            className="rounded border-[#1a3258] bg-[#0a1428] text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Show Grid</span>
        </label>

        <label className="flex items-center gap-2 text-[#cbd5e1] hover:text-white cursor-pointer text-[11.5px]">
          <input
            type="checkbox"
            checked={showBoundingBoxes}
            onChange={(e) => onToggleBoundingBoxes && onToggleBoundingBoxes(e.target.checked)}
            className="rounded border-[#1a3258] bg-[#0a1428] text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Show Bounding Boxes</span>
        </label>

        <label className="flex items-center gap-2 text-[#cbd5e1] hover:text-white cursor-pointer text-[11.5px]">
          <input
            type="checkbox"
            checked={showTrajectory}
            onChange={(e) => onToggleTrajectory && onToggleTrajectory(e.target.checked)}
            className="rounded border-[#1a3258] bg-[#0a1428] text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Show Trajectory</span>
        </label>

        <div className="pt-1">
          <span className="text-[11px] text-[#718eb3] block mb-1">Color by</span>
          <select
            value={colorBy}
            onChange={(e) => onChangeColorBy && onChangeColorBy(e.target.value)}
            className="w-full bg-[#0a1428] border border-[#1a3258] text-white text-[11.5px] rounded px-2 py-1 focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="Semantic Class">Semantic Class</option>
            <option value="Elevation (Z)">Elevation (Z)</option>
            <option value="Intensity">Intensity</option>
            <option value="Resolution">Resolution</option>
          </select>
        </div>
      </div>

      <div className="border-t border-[#14233c]" />

      {/* 5. Map Type */}
      <div className="space-y-1">
        <span className="text-xs font-bold text-white block mb-1">Map Type</span>
        <label className="flex items-center gap-2 text-[#cbd5e1] hover:text-white cursor-pointer text-[11.5px]">
          <input
            type="radio"
            name="mapType"
            value="uniform"
            checked={mapType === 'uniform'}
            onChange={() => onChangeMapType && onChangeMapType('uniform')}
            className="text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Uniform Grid</span>
        </label>
        <label className="flex items-center gap-2 text-white font-medium cursor-pointer text-[11.5px]">
          <input
            type="radio"
            name="mapType"
            value="adaptive"
            checked={mapType === 'adaptive'}
            onChange={() => onChangeMapType && onChangeMapType('adaptive')}
            className="text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Adaptive Grid</span>
        </label>
        <label className="flex items-center gap-2 text-[#cbd5e1] hover:text-white cursor-pointer text-[11.5px]">
          <input
            type="radio"
            name="mapType"
            value="both"
            checked={mapType === 'both'}
            onChange={() => onChangeMapType && onChangeMapType('both')}
            className="text-blue-500 focus:ring-0 focus:outline-none w-3.5 h-3.5 cursor-pointer"
          />
          <span>Both (Comparison)</span>
        </label>
      </div>

      {/* 6. Run Button */}
      <div className="pt-2 mt-auto">
        <button
          onClick={onRunProcessing}
          disabled={isProcessing}
          className="w-full py-2.5 px-3 rounded-md bg-[#e11d48] hover:bg-[#f43f5e] active:scale-[0.98] text-white font-bold text-xs shadow-md shadow-rose-600/30 transition flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
          title="Run entire adaptive perception pipeline"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </>
          ) : (
            <span>Run Processing</span>
          )}
        </button>
      </div>
    </aside>
  );
}
