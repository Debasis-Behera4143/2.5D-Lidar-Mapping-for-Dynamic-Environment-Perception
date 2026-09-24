import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

export default function MiddleViews({ points = [], elevationProfile = {} }) {
  const profileRef = useRef(null);

  // Render Elevation Profile with Plotly.js matching reference screenshot
  useEffect(() => {
    if (!profileRef.current) return;

    const x = elevationProfile.distance_m || Array.from({ length: 101 }, (_, i) => i);
    const y = elevationProfile.height_m || Array.from({ length: 101 }, () => 2.0);

    // Multi-tier elevation gradient traces matching the reference screenshot:
    // Base blue/cyan -> Mid yellow/green -> High red/orange crest
    const yBase = y.map((val) => Math.min(val, 2.0));
    const yMid = y.map((val) => Math.min(val, 4.8));

    const traceBase = {
      x,
      y: yBase,
      type: 'scatter',
      mode: 'none',
      fill: 'tozeroy',
      fillcolor: 'rgba(0, 212, 255, 0.4)',
      hoverinfo: 'none',
      name: 'Base',
    };

    const traceMid = {
      x,
      y: yMid,
      type: 'scatter',
      mode: 'none',
      fill: 'tonexty',
      fillcolor: 'rgba(234, 179, 8, 0.45)',
      hoverinfo: 'none',
      name: 'Mid',
    };

    const traceCrest = {
      x,
      y,
      type: 'scatter',
      mode: 'lines',
      line: {
        color: '#ef4444',
        width: 2.5,
        shape: 'spline',
      },
      fill: 'tonexty',
      fillcolor: 'rgba(239, 68, 68, 0.65)',
      hovertext: x.map((dist, i) => `Dist: ${dist} m<br>Height: ${y[i].toFixed(2)} m`),
      hoverinfo: 'text',
      name: 'Peak Elevation',
    };

    const layout = {
      paper_bgcolor: '#09101f',
      plot_bgcolor: '#09101f',
      margin: { l: 26, r: 10, t: 8, b: 24 },
      xaxis: {
        title: { text: 'Distance (m)', font: { color: '#94a3b8', size: 9 } },
        range: [0, 100],
        dtick: 20,
        gridcolor: '#132035',
        zerolinecolor: '#1e2d48',
        tickfont: { color: '#94a3b8', size: 8 },
      },
      yaxis: {
        title: { text: 'Height (m)', font: { color: '#94a3b8', size: 9 } },
        range: [0, 10],
        dtick: 5,
        gridcolor: '#132035',
        zerolinecolor: '#1e2d48',
        tickfont: { color: '#94a3b8', size: 8 },
      },
      showlegend: false,
    };

    const config = { displayModeBar: false, responsive: true };

    Plotly.react(profileRef.current, [traceBase, traceMid, traceCrest], layout, config);

    const handleResize = () => {
      if (profileRef.current) {
        Plotly.Plots.resize(profileRef.current);
      }
    };
    window.addEventListener('resize', handleResize);
    const ro = new ResizeObserver(handleResize);
    if (profileRef.current) ro.observe(profileRef.current);

    return () => {
      window.removeEventListener('resize', handleResize);
      ro.disconnect();
      if (profileRef.current) {
        Plotly.purge(profileRef.current);
      }
    };
  }, [elevationProfile]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 w-full">
      {/* 1. 2.5D Elevation Map (Side/Front View) */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 pb-1 border-b border-[#172742]">
          <span>2.5D Elevation Map (Side/Front View)</span>
          <span className="text-[10px] text-[#00d4ff] bg-[#00d4ff]/10 px-1 rounded">Cross-Section</span>
        </div>

        <div className="relative w-full h-[150px] bg-[#050913] border border-[#132035] rounded overflow-hidden flex items-center justify-center">
          {/* Side View Canvas */}
          <canvas
            width={380}
            height={150}
            className="w-full h-full object-cover"
            ref={(canvas) => {
              if (!canvas || !points.length) return;
              const w = canvas.parentElement?.clientWidth || 380;
              const h = 150;
              if (canvas.width !== w) canvas.width = w;
              if (canvas.height !== h) canvas.height = h;

              const ctx = canvas.getContext('2d');
              ctx.fillStyle = '#050913';
              ctx.fillRect(0, 0, canvas.width, canvas.height);

              // Road baseline
              ctx.strokeStyle = '#1e3a5f';
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(0, 135);
              ctx.lineTo(canvas.width, 135);
              ctx.stroke();

              const step = Math.max(1, Math.floor(points.length / 1200));
              for (let i = 0; i < points.length; i += step) {
                const pt = points[i];
                // pt[1] is lateral Y (-10 to 12m), pt[2] is height Z (0 to 5m)
                const px = ((pt[1] + 10) / 22) * (canvas.width - 45);
                const py = 135 - (pt[2] / 5.2) * 115;

                // Turbo colormap: height
                const normH = Math.max(0, Math.min(1, pt[2] / 4.8));
                ctx.fillStyle = `hsl(${220 - normH * 220}, 95%, 55%)`;
                ctx.beginPath();
                ctx.arc(px, py, 1.8, 0, Math.PI * 2);
                ctx.fill();
              }
            }}
          />

          {/* Turbo Height Colormap Bar right side matching reference image */}
          <div className="absolute right-2 top-2 bottom-2 flex flex-col items-center justify-between text-[9px] font-mono text-[#cbd5e1] bg-[#09101f]/85 px-1 py-1 rounded border border-[#172742]">
            <div className="text-[8px] text-[#94a3b8] font-sans font-bold">Height (m)</div>
            <div className="text-red-400 font-bold">5.0</div>
            <div
              className="w-2.5 flex-1 mx-auto my-1 rounded-[1px]"
              style={{
                background: 'linear-gradient(to bottom, #ef4444, #eab308, #10b981, #00d4ff, #2563eb)',
              }}
            />
            <div className="text-yellow-400 font-bold">2.5</div>
            <div className="text-blue-400 font-bold">0.0</div>
          </div>
        </div>
      </div>

      {/* 2. Semantic Map (Top View) */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 pb-1 border-b border-[#172742]">
          <span>Semantic Map (Top View)</span>
          <span className="text-[10px] text-emerald-400 bg-emerald-400/10 px-1 rounded">BEV</span>
        </div>

        <div className="relative w-full h-[150px] bg-[#050913] border border-[#132035] rounded overflow-hidden flex items-center justify-center">
          {/* Top-down BEV canvas matching reference image intersection */}
          <canvas
            width={380}
            height={150}
            className="w-full h-full object-cover"
            ref={(canvas) => {
              if (!canvas) return;
              const w = canvas.parentElement?.clientWidth || 380;
              const h = 150;
              if (canvas.width !== w) canvas.width = w;
              if (canvas.height !== h) canvas.height = h;

              const ctx = canvas.getContext('2d');
              ctx.fillStyle = '#050913';
              ctx.fillRect(0, 0, canvas.width, canvas.height);

              const cx = Math.floor(canvas.width / 2) - 15;
              const cy = Math.floor(canvas.height / 2);

              // Background terrain (orange/green)
              ctx.fillStyle = 'rgba(249, 115, 22, 0.35)';
              ctx.fillRect(0, 0, canvas.width, canvas.height);

              // Vegetation clusters (green)
              ctx.fillStyle = '#10b981';
              ctx.beginPath();
              ctx.arc(cx + 65, cy - 40, 20, 0, Math.PI * 2);
              ctx.arc(cx + 90, cy - 30, 16, 0, Math.PI * 2);
              ctx.arc(cx - 75, cy + 45, 22, 0, Math.PI * 2);
              ctx.fill();

              // Road corridor cross (blue #2563eb)
              ctx.fillStyle = '#2563eb';
              ctx.fillRect(0, cy - 25, canvas.width, 50); // Horizontal lane
              ctx.fillRect(cx - 25, 0, 50, canvas.height); // Vertical cross lane

              // Sidewalk margins (purple #8b5cf6)
              ctx.fillStyle = '#8b5cf6';
              ctx.fillRect(0, cy - 32, canvas.width, 7);
              ctx.fillRect(0, cy + 25, canvas.width, 7);

              // Left building wall (red #ef4444)
              ctx.fillStyle = '#ef4444';
              ctx.fillRect(cx - 110, cy - 65, 55, 28);
              ctx.fillRect(cx - 110, cy + 36, 55, 28);

              // Vehicle markers (magenta #d946ef)
              ctx.fillStyle = '#d946ef';
              ctx.fillRect(cx - 5, cy - 50, 10, 16);
              ctx.fillRect(cx + 45, cy - 8, 16, 10);

              // Ego vehicle (white with cyan outline)
              ctx.fillStyle = '#ffffff';
              ctx.strokeStyle = '#00d4ff';
              ctx.lineWidth = 1.5;
              ctx.fillRect(cx - 6, cy + 8, 12, 18);
              ctx.strokeRect(cx - 6, cy + 8, 12, 18);
            }}
          />

          {/* Mini Legend inside Top View right side */}
          <div className="absolute right-1.5 top-1.5 bottom-1.5 bg-[#09101f]/90 border border-[#172742] p-1.5 rounded flex flex-col justify-between text-[8px] text-[#cbd5e1] font-medium pointer-events-none">
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#2563eb]" />
              <span>Road</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#8b5cf6]" />
              <span>Sidewalk</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#ef4444]" />
              <span>Building</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#10b981]" />
              <span>Vegetation</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#d946ef]" />
              <span>Vehicle</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#eab308]" />
              <span>Pedestrian</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#06b6d4]" />
              <span>Pole</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-[1px] bg-[#b45309]" />
              <span>Barrier</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Elevation Profile (Front View) Plotly Area Chart */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 pb-1 border-b border-[#172742]">
          <span>Elevation Profile (Front View)</span>
          <span className="text-[10px] text-rose-400 bg-rose-400/10 px-1 rounded">1D Profile</span>
        </div>

        <div ref={profileRef} className="w-full h-[150px] rounded overflow-hidden" />
      </div>
    </div>
  );
}
