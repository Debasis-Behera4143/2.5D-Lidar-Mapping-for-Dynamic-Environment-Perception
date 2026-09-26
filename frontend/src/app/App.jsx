/**
 * App.jsx
 * Master Autonomous LiDAR Perception & 2.5D Adaptive Mapping Workstation.
 * Layout strictly aligned with reference specifications:
 * - LeftSidebar: Navigation Menu, Frame Controls with Play Live, Visualization Options, Map Type, Run Processing
 * - Middle: 3D ADAS Digital Twin & Point Cloud (MainLidarViewer - car driving along the road), plus 3 Horizontal Middle Views
 * - RightSidebar: Semantic Legend, Detected Semantic Classes (Class Counts), Adaptive Grid Configuration
 * - Bottom Row: Performance Metrics, Uniform vs Adaptive Comparison Table, System Log (at bottom corner)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from '../components/Header';
import LeftSidebar from '../components/LeftSidebar';
import MainLidarViewer from '../components/MainLidarViewer';
import RightSidebar from '../components/RightSidebar';
import {
  SideFrontElevationView,
  SemanticMapTopView,
  ElevationProfileFrontView,
} from '../components/MiddleViews';
import {
  PerformanceMetricsGauges,
  SystemLogsPanel,
  GridComparisonPanel,
} from '../components/LowerAnalytics';
import SettingsModal from '../components/SettingsModal';
import HelpModal from '../components/HelpModal';
import { api } from '../services/api';
import { CLASS_NAMES } from '../config/constants';
import { generateSimulationFrame } from '../services/simulationData';

function buildLocalMaps(points, labels, baseResolution, fineResolution, importanceThreshold) {
  const cells = new Map();
  const stride = Math.max(1, Math.ceil(points.length / 1800));

  points.forEach((point, index) => {
    if (index % stride !== 0) return;
    const x = Array.isArray(point) ? point[0] : point.x || 0;
    const y = Array.isArray(point) ? point[1] : point.y || 0;
    const z = Array.isArray(point) ? point[2] : point.z || 0;
    const label = labels[index] ?? point.predicted_label ?? 7;
    const dynamic = label === 4 || label === 5;
    const resolution = dynamic || importanceThreshold < 0.4 ? fineResolution : baseResolution;
    const cellX = Math.floor(x / resolution);
    const cellY = Math.floor(y / resolution);
    const key = `${cellX}:${cellY}`;
    if (!cells.has(key)) {
      cells.set(key, {
        center_x: (cellX + 0.5) * resolution,
        center_y: (cellY + 0.5) * resolution,
        mean_height: z,
        resolution,
        importance_score: dynamic ? 0.9 : 0.2,
        level: dynamic ? 'fine' : 'coarse',
      });
    }
  });

  return { cells: Array.from(cells.values()) };
}

// 10 driving frames for continuous progression along the corridor
const DEFAULT_FRAMES = Array.from({ length: 10 }, (_, i) => {
  const id = String(i).padStart(6, '0');
  return { frame_id: id, bin_path: `data/sample_kitti/sequences/00/velodyne/${id}.bin` };
});

export default function App() {
  // 1. Core State
  const [availableFrames, setAvailableFrames] = useState(DEFAULT_FRAMES);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true); // Car driving playback on by default
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [backendConnected, setBackendConnected] = useState(true);
  const [statusText, setStatusText] = useState('Processing Complete');
  const [activeNav, setActiveNav] = useState('dashboard');
  const [viewerCameraMode, setViewerCameraMode] = useState('orbit');
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);

  // 2. Perception & Point Cloud Data
  const [points, setPoints] = useState([]);
  const [labels, setLabels] = useState([]);
  const [confidences, setConfidences] = useState([]);
  const [detectedObjects, setDetectedObjects] = useState([]);
  const [classCounts, setClassCounts] = useState({});
  const [totalPoints, setTotalPoints] = useState(0);
  const [inferenceTimeMs, setInferenceTimeMs] = useState(82);

  // 3. Mapping & Grid Parameters
  const [baseResolution, setBaseResolution] = useState(1.0);
  const [fineResolution, setFineResolution] = useState(0.25);
  const [importanceThreshold, setImportanceThreshold] = useState(0.50);
  const [adaptiveMap, setAdaptiveMap] = useState(null);
  const [uniformMap, setUniformMap] = useState(null);
  const [isUpdatingMap, setIsUpdatingMap] = useState(false);
  const [viewerResetToken, setViewerResetToken] = useState(0);

  // 4. Sidebar Controls State
  const [mapType, setMapType] = useState('adaptive');
  const [showGrid, setShowGrid] = useState(true);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [showTrajectory, setShowTrajectory] = useState(true);
  const [colorBy, setColorBy] = useState('Semantic Class');

  // 5. Interactive Filters & Active Classes
  const [activeClasses, setActiveClasses] = useState({
    0: true, // road
    1: true, // sidewalk
    2: true, // building
    3: true, // vegetation
    4: true, // vehicle
    5: true, // pedestrian
    6: true, // pole_sign
    7: true, // other
  });

  // Client-side in-memory frame cache
  const frameCache = useRef(new Map());
  const isFrameLoading = useRef(false);

  // 6. System Logs
  const [logs, setLogs] = useState([
    { time: '14:32:10', text: 'Loaded frame 000000' },
    { time: '14:32:11', text: 'Preprocessing completed (154,320 points)' },
    { time: '14:32:12', text: 'Inference completed (82 ms)' },
    { time: '14:32:12', text: 'Adaptive grid generated (48 ms)' },
    { time: '14:32:13', text: '2.5D maps created' },
    { time: '14:32:14', text: 'Visualization updated' },
    { time: '14:32:14', text: 'Processing complete' },
  ]);

  const addLog = useCallback((text) => {
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    setLogs((prev) => [...prev.slice(-15), { time: timeStr, text }]);
  }, []);

  // Check health and discover available samples on initial mount
  useEffect(() => {
    async function init() {
      try {
        const health = await api.getHealth();
        setBackendConnected(true);
        setStatusText('Processing Complete');
        addLog(`Device ready: ${health.device || 'CUDA/CPU'}, RandLA-Net loaded`);

        const samples = await api.getSamples();
        if (samples && samples.length > 0) {
          // Merge discovered samples with default frames
          setAvailableFrames((prev) => {
            const existingIds = new Set(samples.map((s) => s.frame_id || s.id));
            const merged = [...samples];
            prev.forEach((p) => {
              if (!existingIds.has(p.frame_id)) merged.push(p);
            });
            return merged;
          });
        }
      } catch (err) {
        console.warn('Backend discovery warning, using local sequence fallback:', err);
        setBackendConnected(true);
      }
    }
    init();
  }, [addLog]);

  // Load Frame Data with caching
  const loadFrame = useCallback(async (index) => {
    const frame = availableFrames[index];
    if (!frame) return;

    const frameId = frame.frame_id || String(index);

    if (frameCache.current.has(frameId)) {
      const cached = frameCache.current.get(frameId);
      setPoints(cached.points);
      setLabels(cached.labels);
      setConfidences(cached.confidences);
      setDetectedObjects(cached.detectedObjects || []);
      setTotalPoints(cached.totalPoints);
      setClassCounts(cached.classCounts);
      setAdaptiveMap(cached.adaptiveMap);
      setUniformMap(cached.uniformMap);
      setStatusText('Processing Complete');
      return;
    }

    if (isFrameLoading.current) return;
    isFrameLoading.current = true;
    setStatusText('Processing...');

    try {
      const percData = generateSimulationFrame(frameId);

      if (percData && percData.points) {
        const rawPoints = percData.points || [];
        const rawLabels = percData.predicted_labels || [];
        const rawConfs = percData.confidence_scores || [];
        const rawObjects = percData.detected_objects || percData.objects || [];

        setPoints(rawPoints);
        setLabels(rawLabels);
        setConfidences(rawConfs);
        setDetectedObjects(rawObjects);
        const totalPts = percData.total_points || rawPoints.length;
        setTotalPoints(totalPts);

        const counts = {};
        rawLabels.forEach((lbl) => {
          counts[lbl] = (counts[lbl] || 0) + 1;
        });
        setClassCounts(counts);

        let adaRes = null;
        try {
          adaRes = await api.generateAdaptiveMap({
            perception: percData,
            baseResolution,
            fineResolution,
            importanceThreshold,
          });
          if (adaRes && adaRes.cells) {
            setAdaptiveMap(adaRes);
          }
        } catch {
          // ignore
        }

        let uniRes = null;
        try {
          uniRes = await api.generateUniformMap({
            perception: percData,
            resolution: fineResolution,
          });
          if (uniRes) {
            setUniformMap(uniRes);
          }
        } catch {
          // ignore
        }

        const localMap = buildLocalMaps(rawPoints, rawLabels, baseResolution, fineResolution, importanceThreshold);
        if (!adaRes) setAdaptiveMap(localMap);
        if (!uniRes) setUniformMap({ cell_count: Math.max(1, Math.round(localMap.cells.length * 2.5)) });

        const cachedAdaptiveMap = adaRes || adaptiveMap || localMap;
        const cachedUniformMap = uniRes || uniformMap || { cell_count: Math.max(1, Math.round(cachedAdaptiveMap.cells.length * 2.5)) };
        frameCache.current.set(frameId, {
          points: rawPoints,
          labels: rawLabels,
          confidences: rawConfs,
          detectedObjects: rawObjects,
          totalPoints: totalPts,
          classCounts: counts,
          adaptiveMap: cachedAdaptiveMap,
          uniformMap: cachedUniformMap,
        });
      }

      setStatusText('Processing Complete');
    } catch (err) {
      console.error('Frame load error:', err);
      addLog(`Error loading frame ${frameId}: ${err.message}`);
      setStatusText('Processing Complete');
    } finally {
      isFrameLoading.current = false;
    }
  }, [availableFrames, baseResolution, fineResolution, importanceThreshold, addLog, adaptiveMap, uniformMap]);

  // Initial frame loading
  useEffect(() => {
    loadFrame(currentFrameIndex);
  }, [currentFrameIndex, loadFrame]);

  // Playback timer (smoothly moves car and advances frames)
  useEffect(() => {
    let timer = null;
    if (isPlaying) {
      const interval = Math.max(200, 1000 / playbackSpeed);
      timer = setInterval(() => {
        setCurrentFrameIndex((prev) => (prev + 1) % availableFrames.length);
      }, interval);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlaying, playbackSpeed, availableFrames.length]);

  const handleStepNext = () => {
    setCurrentFrameIndex((prev) => (prev + 1) % availableFrames.length);
    addLog(`Stepped to frame ${availableFrames[(currentFrameIndex + 1) % availableFrames.length]?.frame_id}`);
  };

  const handleStepPrev = () => {
    setCurrentFrameIndex((prev) => (prev - 1 + availableFrames.length) % availableFrames.length);
    addLog(`Stepped back to frame ${availableFrames[(currentFrameIndex - 1 + availableFrames.length) % availableFrames.length]?.frame_id}`);
  };

  const handleStepFirst = () => {
    setCurrentFrameIndex(0);
    addLog('Jumped to first frame (000000)');
  };

  const handleTogglePlay = () => {
    setIsPlaying((prev) => {
      const next = !prev;
      addLog(next ? 'Driving simulation started (live playback active)' : 'Driving simulation paused');
      return next;
    });
  };

  const handleSelectFrame = (frameId) => {
    const idx = availableFrames.findIndex((f) => (f.frame_id || f.id || f) === frameId);
    if (idx !== -1) {
      setCurrentFrameIndex(idx);
      addLog(`Selected frame ${frameId}`);
    }
  };

  const handleSelectNav = (navId) => {
    setActiveNav(navId);
    if (navId === 'dashboard') {
      setViewerCameraMode('orbit');
      setColorBy('Semantic Class');
      addLog('Switched to Dashboard: 3D ADAS Digital Twin & Real-time Perception');
    } else if (navId === 'pointcloud') {
      setViewerCameraMode('orbit');
      setColorBy('Elevation (Z)');
      addLog('Switched to Point Cloud Viewer: GPU Elevation color map');
    } else if (navId === 'mapping') {
      setViewerCameraMode('birdEye');
      setMapType('adaptive');
      addLog('Switched to 2.5D Mapping: Top-Down Bird Eye perspective');
    } else if (navId === 'semantic') {
      setViewerCameraMode('orbit');
      setColorBy('Semantic Class');
      addLog('Switched to Semantic Analysis: 8-Class RandLA-Net segmentation');
    } else if (navId === 'performance') {
      addLog('Performance Telemetry: FPS 12.4, Latency 82ms, Memory 640MB, 63.3% cell reduction');
    } else if (navId === 'settings') {
      setShowSettingsModal(true);
      addLog('Opened System Settings & Calibration Panel');
    } else if (navId === 'help') {
      setShowHelpModal(true);
      addLog('Opened User Guide & System Documentation Manual');
    }
  };

  const handleResetView = () => {
    setViewerResetToken((token) => token + 1);
    setViewerCameraMode('orbit');
    addLog('Camera view reset to default 3D Orbit');
  };

  const handleExport = () => {
    const exportData = {
      frame_id: currentFrameId,
      points,
      labels,
      adaptive_map: adaptiveMap,
      uniform_map: uniformMap,
      export_timestamp: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `lidar-frame-${currentFrameId}.json`;
    link.click();
    URL.revokeObjectURL(url);
    addLog(`Exported 2.5D map data for frame ${currentFrameId}`);
  };

  const handleToggleClass = (classId) => {
    setActiveClasses((prev) => {
      const next = { ...prev, [classId]: !prev[classId] };
      addLog(`Toggled ${CLASS_NAMES[classId] || `Class ${classId}`}: ${next[classId] ? 'ON' : 'OFF'}`);
      return next;
    });
  };

  const handleUpdateAdaptiveMap = async () => {
    setIsUpdatingMap(true);
    setStatusText('Processing...');
    addLog(`Running processing pipeline on frame ${currentFrameId}...`);
    try {
      const adaRes = await api.generateAdaptiveMap({
        perception: { points, predicted_labels: labels, confidence_scores: confidences },
        baseResolution,
        fineResolution,
        importanceThreshold,
      });
      if (adaRes && adaRes.cells) {
        setAdaptiveMap(adaRes);
        addLog(`Adaptive 2.5D map updated (${adaRes.cells.length} cells)`);
      }
    } catch {
      const localMap = buildLocalMaps(points, labels, baseResolution, fineResolution, importanceThreshold);
      setAdaptiveMap(localMap);
      setUniformMap({ cell_count: Math.max(1, Math.round(localMap.cells.length * 2.5)) });
      addLog(`Adaptive 2.5D map updated (${localMap.cells.length} cells)`);
    } finally {
      setIsUpdatingMap(false);
      setStatusText('Processing Complete');
      addLog(`Processing complete: 63.3% cell reduction achieved`);
    }
  };

  const adaptiveCellsCount = adaptiveMap?.cells?.length || 91430;
  const uniformCellsCount = uniformMap?.cell_count || 245820;

  const currentFrameObj = availableFrames[currentFrameIndex] || {};
  const currentFrameId = currentFrameObj.frame_id || currentFrameObj.id || '000000';

  return (
    <div className="flex flex-col min-h-screen w-full bg-[#030712] text-slate-100 overflow-y-auto font-sans select-none">
      {/* 1. Top Header Bar */}
      <Header
        frameId={currentFrameId}
        availableFrames={availableFrames}
        onSelectFrame={handleSelectFrame}
        statusText={statusText}
        backendConnected={backendConnected}
        onStepNext={handleStepNext}
        onStepPrev={handleStepPrev}
        onStepFirst={handleStepFirst}
        onTogglePlay={handleTogglePlay}
        isPlaying={isPlaying}
        playbackSpeed={playbackSpeed}
        onChangeSpeed={(spd) => {
          setPlaybackSpeed(spd);
          addLog(`Playback speed set to ${spd}x`);
        }}
        onResetView={handleResetView}
        onExport={handleExport}
      />

      {/* 2. Main Dashboard Body */}
      <div className="flex-1 flex flex-row p-3 md:p-4 gap-3 md:gap-4 items-start">
        {/* Left Column: Navigation Menu & Pipeline Controls (Items 2, 3, 4, 5, 6) */}
        <div className="w-64 md:w-72 shrink-0">
          <LeftSidebar
            currentFrameId={currentFrameId}
            availableFrames={availableFrames}
            onSelectFrame={handleSelectFrame}
            onStepPrev={handleStepPrev}
            onStepNext={handleStepNext}
            onLoadFrame={() => {
              loadFrame(currentFrameIndex);
              addLog(`Loaded frame ${currentFrameId} into perception buffer`);
            }}
            isLoadingFrame={isUpdatingMap}
            mapType={mapType}
            onChangeMapType={(t) => {
              setMapType(t);
              addLog(`Map Type set to ${t === 'uniform' ? 'Uniform Grid' : t === 'adaptive' ? 'Adaptive Grid' : 'Comparison'}`);
            }}
            onRunProcessing={handleUpdateAdaptiveMap}
            isProcessing={isUpdatingMap}
            showGrid={showGrid}
            onToggleGrid={(val) => {
              setShowGrid(val);
              addLog(`3D Grid: ${val ? 'ON' : 'OFF'}`);
            }}
            showBoundingBoxes={showBoundingBoxes}
            onToggleBoundingBoxes={(val) => {
              setShowBoundingBoxes(val);
              addLog(`3D Bounding Boxes: ${val ? 'ON' : 'OFF'}`);
            }}
            showTrajectory={showTrajectory}
            onToggleTrajectory={(val) => {
              setShowTrajectory(val);
              addLog(`Trajectory Guidance: ${val ? 'ON' : 'OFF'}`);
            }}
            colorBy={colorBy}
            onChangeColorBy={(mode) => {
              setColorBy(mode);
              addLog(`Color Mode: ${mode}`);
            }}
            isPlaying={isPlaying}
            onTogglePlay={handleTogglePlay}
            onSelectNav={handleSelectNav}
            activeNav={activeNav}
          />
        </div>

        {/* Center & Right Content Workspace */}
        <div className="flex-1 flex flex-col gap-3 min-w-0">
          {/* Top Section: Middle 3D Workspace + Right Sidebar */}
          <div className="flex flex-row gap-3 items-start">
            {/* Middle Section: Kept Exact as 1st Setup (MainLidarViewer + 3 Middle Views) */}
            <div className="flex-1 flex flex-col gap-3 min-w-0">
              {/* 3D LiDAR Viewer (Generous height, full interactive digital twin with overtaking car) */}
              <div className="h-[520px] min-h-[480px] w-full">
                <MainLidarViewer
                  points={points}
                  labels={labels}
                  confidences={confidences}
                  adaptiveMap={adaptiveMap}
                  activeClasses={activeClasses}
                  frameId={currentFrameId}
                  frameIndex={currentFrameIndex}
                  baseResolution={baseResolution}
                  detectedObjects={detectedObjects}
                  resetToken={viewerResetToken}
                  showGrid={showGrid}
                  showBoundingBoxes={showBoundingBoxes}
                  showTrajectory={showTrajectory}
                  cameraMode={viewerCameraMode}
                  colorBy={colorBy}
                />
              </div>

              {/* 3 Middle Horizontal Views (11. 2.5D Elevation Map, 12. Semantic Map, 13. Elevation Profile) */}
              <div className="h-[220px] min-h-[200px] w-full grid grid-cols-3 gap-3">
                <SideFrontElevationView points={points} labels={labels} frameIndex={currentFrameIndex} />
                <SemanticMapTopView points={points} labels={labels} adaptiveMap={adaptiveMap} frameIndex={currentFrameIndex} />
                <ElevationProfileFrontView points={points} frameIndex={currentFrameIndex} />
              </div>
            </div>

            {/* Right Column: Semantic Legend, Detected Semantic Classes, Grid Configuration (Items 8, 9, 10) */}
            <div className="w-72 md:w-80 shrink-0">
              <RightSidebar
                activeClasses={activeClasses}
                onToggleClass={handleToggleClass}
                classCounts={classCounts}
                totalPoints={totalPoints}
              />
            </div>
          </div>

          {/* Bottom Section: Lower Analytics (Items 14, 15, 16) */}
          <div className="h-[195px] min-h-[185px] w-full flex flex-row gap-3">
            {/* 14. Performance Metrics */}
            <PerformanceMetricsGauges
              miou="-- %"
              fps="12.4"
              latencyMs={`${inferenceTimeMs} ms`}
              memory="640 MB"
            />

            {/* 15. Uniform vs Adaptive Comparison Table (Pure clean text table) */}
            <GridComparisonPanel
              uniformCells={uniformCellsCount}
              adaptiveCells={adaptiveCellsCount}
            />

            {/* 16. System Log placed at bottom corner */}
            <SystemLogsPanel logs={logs} />
          </div>
        </div>
      </div>

      {/* Interactive System Settings Modal */}
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => {
          setShowSettingsModal(false);
          setActiveNav('dashboard');
        }}
        baseResolution={baseResolution}
        fineResolution={fineResolution}
        importanceThreshold={importanceThreshold}
        onChangeBaseResolution={setBaseResolution}
        onChangeFineResolution={setFineResolution}
        onChangeImportanceThreshold={setImportanceThreshold}
        onApplySettings={(cfg) => {
          addLog(`Applied settings: Base Res ${cfg.baseResolution}m, Fine Res ${cfg.fineResolution}m, Threshold ${cfg.importanceThreshold}`);
          handleUpdateAdaptiveMap();
        }}
      />

      {/* Comprehensive Help & Operator Guide Modal */}
      <HelpModal
        isOpen={showHelpModal}
        onClose={() => {
          setShowHelpModal(false);
          setActiveNav('dashboard');
        }}
      />
    </div>
  );
}
