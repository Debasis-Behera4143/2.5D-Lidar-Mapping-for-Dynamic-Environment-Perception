/**
 * Sidebar.jsx
 * Left technical column container with navigation tabs, real frame playback, and perception controls.
 */

import React from 'react';
import { Play, Pause, SkipBack, SkipForward, Sliders, Brain, Map, Cpu } from 'lucide-react';
import SceneOverview from './SceneOverview';
import AISemanticPanel from './AISemanticPanel';
import AdaptiveMappingPanel from './AdaptiveMappingPanel';

export default function Sidebar({
  samples = [],
  currentSampleId,
  onSelectSample,
  isPlaying,
  onTogglePlay,
  onStepNext,
  onStepPrev,
  playbackSpeed,
  onChangeSpeed,
  activeTab = 'overview',
  onSelectTab,
  sceneOverviewData,
  inferenceData,
  mappingConfig,
  onUpdateMappingConfig,
  onRunMapping,
  mappingLoading,
  inferenceLoading,
}) {
  return (
    <aside className="w-80 bg-[#070b16] border-r border-slate-800 flex flex-col h-[calc(100vh-3.25rem)] overflow-hidden select-none">
      {/* 1. Real Sequence & Frame Playback Controller */}
      <div className="p-3 bg-[#0a101f] border-b border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            LiDAR Frame Sequence
          </span>
          <select
            value={currentSampleId || ''}
            onChange={(e) => onSelectSample(e.target.value)}
            className="bg-[#0f172a] border border-slate-700 text-slate-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-blue-500 font-mono-num max-w-[140px]"
          >
            {samples.map((s) => (
              <option key={s.sample_id} value={s.sample_id}>
                {s.frame_id || s.sample_id} ({s.dataset_type || 'KITTI'})
              </option>
            ))}
          </select>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-between gap-1 bg-[#050811] p-1.5 rounded border border-slate-800">
          <div className="flex items-center gap-1">
            <button
              onClick={onStepPrev}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
              title="Previous Frame"
            >
              <SkipBack className="w-4 h-4" />
            </button>
            <button
              onClick={onTogglePlay}
              className={`p-1.5 rounded font-bold flex items-center justify-center transition ${
                isPlaying
                  ? 'bg-amber-600 text-white hover:bg-amber-500'
                  : 'bg-blue-600 text-white hover:bg-blue-500'
              }`}
              title={isPlaying ? 'Pause Playback' : 'Play Sequence'}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
            </button>
            <button
              onClick={onStepNext}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
              title="Next Frame"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 text-[11px] font-mono-num text-slate-400">
            <span className="text-[10px]">Speed:</span>
            {[1, 2, 4].map((spd) => (
              <button
                key={spd}
                onClick={() => onChangeSpeed(spd)}
                className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                  playbackSpeed === spd
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Left Column Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-[#090e1c]">
        {[
          { id: 'overview', label: 'Scene', icon: Cpu },
          { id: 'ai', label: 'AI Segmentation', icon: Brain },
          { id: 'mapping', label: 'Adaptive Grid', icon: Map },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => onSelectTab(t.id)}
              className={`flex-1 py-2 text-xs font-semibold flex items-center justify-center gap-1.5 border-b-2 transition ${
                isActive
                  ? 'border-blue-500 text-blue-400 bg-[#0d152a]'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-[#0c1224]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* 3. Tab Contents with Scroll */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {activeTab === 'overview' && (
          <SceneOverview
            data={sceneOverviewData}
            inferenceData={inferenceData}
          />
        )}

        {activeTab === 'ai' && (
          <AISemanticPanel
            inferenceData={inferenceData}
            loading={inferenceLoading}
          />
        )}

        {activeTab === 'mapping' && (
          <AdaptiveMappingPanel
            config={mappingConfig}
            onChangeConfig={onUpdateMappingConfig}
            onRunMapping={onRunMapping}
            loading={mappingLoading}
          />
        )}
      </div>
    </aside>
  );
}
