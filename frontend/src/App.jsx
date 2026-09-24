import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import SceneOverview from './components/SceneOverview';
import MainLidarViewer from './components/MainLidarViewer';
import RightPanels from './components/RightPanels';
import MiddleViews from './components/MiddleViews';
import LowerAnalytics from './components/LowerAnalytics';
import FooterBar from './components/FooterBar';
import { apiService } from './services/api';
import { SIMULATION_FRAMES } from './config/constants';

export default function App() {
  const [selectedFrame, setSelectedFrame] = useState('1248');
  const [frameData, setFrameData] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [dataSource, setDataSource] = useState('Simulation');
  const [colorMode, setColorMode] = useState('semantic');
  const [backendOnline, setBackendOnline] = useState(false);
  const [pingMs, setPingMs] = useState(null);

  // Initial Health Check & Data Load
  useEffect(() => {
    let isMounted = true;

    async function checkBackend() {
      const start = performance.now();
      const health = await apiService.checkHealth();
      const ping = Math.round(performance.now() - start);

      if (isMounted) {
        setBackendOnline(health.online || false);
        setPingMs(ping);
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Ingest Frame Data whenever selectedFrame or dataSource changes
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      const data = await apiService.getFrameData(selectedFrame, dataSource);
      if (isMounted) {
        setFrameData(data);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [selectedFrame, dataSource]);

  // Continuous Playback Animation Timer
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setSelectedFrame((prev) => {
        const idx = SIMULATION_FRAMES.findIndex((f) => f.id === prev);
        const nextIdx = (idx + 1) % SIMULATION_FRAMES.length;
        return SIMULATION_FRAMES[nextIdx].id;
      });
    }, 2500);

    return () => clearInterval(timer);
  }, [isPlaying]);

  const handleTogglePlay = () => {
    setIsPlaying((prev) => !prev);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setSelectedFrame('1248');
    setColorMode('semantic');
  };

  const handleToggleDataSource = () => {
    setDataSource((prev) => (prev === 'Simulation' ? 'FastAPI' : 'Simulation'));
  };

  const handleToggleColorMode = () => {
    setColorMode((prev) => (prev === 'semantic' ? 'elevation' : 'semantic'));
  };

  if (!frameData) {
    return (
      <div className="w-screen h-screen bg-[#050913] flex flex-col items-center justify-center text-white">
        <div className="w-10 h-10 border-2 border-[#00d4ff] border-t-transparent rounded-full animate-spin mb-3" />
        <div className="text-sm font-semibold tracking-wide">Initializing 2.5D LiDAR Perception Engine...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050913] text-[#f8fafc] flex flex-col justify-between selection:bg-[#00d4ff]/30 selection:text-white">
      {/* Top Application Header */}
      <Header
        selectedFrame={selectedFrame}
        onSelectFrame={setSelectedFrame}
        isPlaying={isPlaying}
        onTogglePlay={handleTogglePlay}
        onReset={handleReset}
        dataSource={dataSource}
        onToggleDataSource={handleToggleDataSource}
        backendOnline={backendOnline}
        pingMs={pingMs}
      />

      {/* Main Workstation Canvas Area */}
      <main className="flex-1 p-3 flex flex-col gap-3 max-w-[1920px] mx-auto w-full">
        {/* ROW 1: PRIMARY 3-COLUMN WORKSTATION VIEW */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-start">
          {/* Left Column (Scene Overview Pipeline) */}
          <div className="lg:col-span-2">
            <SceneOverview points={frameData.points} />
          </div>

          {/* Center Column (Hero 3D LiDAR & 2.5D Elevation Map) */}
          <div className="lg:col-span-7">
            <MainLidarViewer
              points={frameData.points}
              labels={frameData.predicted_labels}
              annotations={frameData.annotations}
              colorMode={colorMode}
              onToggleColorMode={handleToggleColorMode}
            />
          </div>

          {/* Right Column (Semantic Legend, Objects, Resolution) */}
          <div className="lg:col-span-3">
            <RightPanels sceneObjects={frameData.scene_objects} />
          </div>
        </div>

        {/* ROW 2: SUB-VIEWPORT PERCEPTION MAPS */}
        <div className="w-full">
          <MiddleViews
            points={frameData.points}
            elevationProfile={frameData.elevation_profile}
          />
        </div>

        {/* ROW 3: PERFORMANCE METRICS, SYSTEM LOGS & GRID COMPARISON */}
        <div className="w-full">
          <LowerAnalytics
            performance={frameData.performance}
            logs={frameData.system_logs}
            gridComparison={frameData.grid_comparison}
          />
        </div>

        {/* ROW 4: BOTTOM SUMMARY STRIP */}
        <div className="w-full">
          <FooterBar />
        </div>
      </main>
    </div>
  );
}
