import React from 'react';
import { Activity, Terminal, Grid3X3 } from 'lucide-react';

export default function LowerAnalytics({
  performance = {},
  logs = [],
  gridComparison = {},
}) {
  const kpis = [
    {
      label: 'mIoU (Semantic Seg.)',
      val: `${performance.miou_percent || 87}%`,
      pct: performance.miou_percent || 87,
      color: '#10b981',
      badge: performance.provenance || 'SIMULATION',
    },
    {
      label: 'FPS',
      val: `${performance.fps || 18}`,
      pct: Math.min(100, (performance.fps || 18) * 4),
      color: '#38bdf8',
      badge: performance.provenance || 'SIMULATION',
    },
    {
      label: 'Latency',
      val: `${performance.latency_ms || 55} ms`,
      pct: Math.min(100, (performance.latency_ms || 55) * 1.2),
      color: '#a855f7',
      badge: performance.provenance || 'SIMULATION',
    },
    {
      label: 'Memory Usage',
      val: `${performance.memory_mb || 820} MB`,
      pct: Math.min(100, ((performance.memory_mb || 820) / 1024) * 100),
      color: '#f97316',
      badge: performance.provenance || 'SIMULATION',
    },
  ];

  const circumference = 2 * Math.PI * 26; // r = 26

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 w-full">
      {/* 1. Performance Metrics (5 Columns on Desktop) */}
      <div className="lg:col-span-5 bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-2 pb-1 border-b border-[#172742]">
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#00d4ff]" />
            <span>Performance Metrics</span>
          </div>
          <span className="text-[10px] text-amber-400 bg-amber-400/10 px-1.5 py-0.2 rounded border border-amber-400/30">
            {performance.provenance || 'SIMULATION'}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 h-full items-center">
          {kpis.map((kpi) => {
            const offset = circumference * (1 - Math.max(0, Math.min(1, kpi.pct / 100)));
            return (
              <div key={kpi.label} className="flex flex-col items-center justify-center p-1 rounded bg-[#050913]/60 border border-[#172742]">
                <div className="text-[10px] text-[#94a3b8] font-medium text-center h-6 flex items-center justify-center">
                  {kpi.label}
                </div>

                {/* Circular SVG Ring Gauge */}
                <div className="relative w-[64px] h-[64px] my-1 flex items-center justify-center">
                  <svg className="w-[64px] h-[64px] -rotate-90">
                    <circle cx="32" cy="32" r="26" stroke="#132238" strokeWidth="5.5" fill="none" />
                    <circle
                      cx="32"
                      cy="32"
                      r="26"
                      stroke={kpi.color}
                      strokeWidth="5.5"
                      fill="none"
                      strokeDasharray={circumference}
                      strokeDashoffset={offset}
                      strokeLinecap="round"
                      className="transition-all duration-700 ease-out"
                    />
                  </svg>
                  <span className="absolute font-mono font-bold text-xs text-white tracking-tighter">
                    {kpi.val}
                  </span>
                </div>

                <span className="text-[8px] font-semibold text-[#64748b] uppercase tracking-wider">
                  {kpi.badge}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. System Logs (3 Columns on Desktop) */}
      <div className="lg:col-span-3 bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 pb-1 border-b border-[#172742]">
          <div className="flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-[#a855f7]" />
            <span>System Logs</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono">18 FPS</span>
        </div>

        <div className="flex-1 bg-[#050913] rounded border border-[#132035] p-2 font-mono text-[10px] space-y-1 overflow-y-auto max-h-[110px]">
          {logs.map((log, idx) => (
            <div key={idx} className="flex items-start gap-2 leading-relaxed">
              <span className="text-[#38bdf8] select-none">{log.time}</span>
              <span className="text-[#e2e8f0]">{log.msg}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Grid Comparison (4 Columns on Desktop) */}
      <div className="lg:col-span-4 bg-[#09101f] border border-[#172742] rounded-md p-2.5 flex flex-col shadow-md">
        <div className="flex items-center justify-between text-xs font-bold text-white mb-1.5 pb-1 border-b border-[#172742]">
          <div className="flex items-center gap-1.5">
            <Grid3X3 className="w-3.5 h-3.5 text-[#00d4ff]" />
            <span>Grid Comparison</span>
          </div>
          <span className="text-[10px] text-emerald-400 bg-emerald-400/10 px-1.5 py-0.2 rounded border border-emerald-400/30">
            -68.3% CELLS
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 flex-1">
          {/* Uniform Grid Preview */}
          <div className="bg-[#050913] border border-[#132035] rounded p-1.5 flex flex-col items-center">
            <span className="text-[10px] font-semibold text-[#94a3b8] mb-1">Uniform Grid (5 cm)</span>
            <div className="w-full h-[66px] bg-[#050913] rounded border border-[#1e293b] flex items-center justify-center relative overflow-hidden">
              <canvas
                width={180}
                height={66}
                className="w-full h-full object-cover"
                ref={(canvas) => {
                  if (!canvas) return;
                  const w = canvas.parentElement?.clientWidth || 180;
                  if (canvas.width !== w) canvas.width = w;

                  const ctx = canvas.getContext('2d');
                  ctx.fillStyle = '#050913';
                  ctx.fillRect(0, 0, canvas.width, canvas.height);

                  const cx = Math.floor(canvas.width / 2);

                  // Base terrain and road
                  ctx.fillStyle = 'rgba(249, 115, 22, 0.25)';
                  ctx.fillRect(0, 0, canvas.width, canvas.height);
                  ctx.fillStyle = '#1e3a8a';
                  ctx.fillRect(0, 22, canvas.width, 22);
                  ctx.fillRect(cx - 10, 0, 20, canvas.height);

                  // Vehicle marker
                  ctx.fillStyle = '#d946ef';
                  ctx.fillRect(cx - 4, 30, 8, 10);

                  // Uniform fine grid across entirety
                  ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
                  ctx.lineWidth = 0.5;
                  for (let x = 0; x < canvas.width; x += 5) {
                    ctx.beginPath();
                    ctx.moveTo(x, 0);
                    ctx.lineTo(x, canvas.height);
                    ctx.stroke();
                  }
                  for (let y = 0; y < canvas.height; y += 5) {
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(canvas.width, y);
                    ctx.stroke();
                  }
                }}
              />
              <span className="absolute bottom-1 right-1 text-[8px] font-mono font-bold bg-[#09101f]/85 px-1 rounded text-[#38bdf8] border border-[#172742]">
                14,280 cells
              </span>
            </div>
            <span className="text-[9px] text-[#64748b] mt-1">Equal spatial resolution</span>
          </div>

          {/* Adaptive Grid Preview */}
          <div className="bg-[#050913] border border-[#132035] rounded p-1.5 flex flex-col items-center">
            <span className="text-[10px] font-semibold text-[#00d4ff] mb-1">Adaptive Grid</span>
            <div className="w-full h-[66px] bg-[#050913] rounded border border-[#00d4ff]/40 flex items-center justify-center relative overflow-hidden">
              <canvas
                width={180}
                height={66}
                className="w-full h-full object-cover"
                ref={(canvas) => {
                  if (!canvas) return;
                  const w = canvas.parentElement?.clientWidth || 180;
                  if (canvas.width !== w) canvas.width = w;

                  const ctx = canvas.getContext('2d');
                  ctx.fillStyle = '#050913';
                  ctx.fillRect(0, 0, canvas.width, canvas.height);

                  const cx = Math.floor(canvas.width / 2);

                  // Base terrain and road
                  ctx.fillStyle = 'rgba(249, 115, 22, 0.25)';
                  ctx.fillRect(0, 0, canvas.width, canvas.height);
                  ctx.fillStyle = '#1e3a8a';
                  ctx.fillRect(0, 22, canvas.width, 22);
                  ctx.fillRect(cx - 10, 0, 20, canvas.height);

                  // Vehicle marker
                  ctx.fillStyle = '#d946ef';
                  ctx.fillRect(cx - 4, 30, 8, 10);

                  // 1. Coarse grid on periphery (step = 20)
                  ctx.strokeStyle = 'rgba(249, 115, 22, 0.45)';
                  ctx.lineWidth = 0.8;
                  for (let x = 0; x < canvas.width; x += 20) {
                    ctx.beginPath();
                    ctx.moveTo(x, 0);
                    ctx.lineTo(x, canvas.height);
                    ctx.stroke();
                  }
                  for (let y = 0; y < canvas.height; y += 20) {
                    ctx.beginPath();
                    ctx.moveTo(0, y);
                    ctx.lineTo(canvas.width, y);
                    ctx.stroke();
                  }

                  // 2. Mid grid on road corridors (step = 10)
                  ctx.strokeStyle = 'rgba(168, 85, 247, 0.55)';
                  ctx.lineWidth = 0.6;
                  for (let x = Math.max(0, cx - 40); x <= Math.min(canvas.width, cx + 40); x += 10) {
                    ctx.beginPath();
                    ctx.moveTo(x, 10);
                    ctx.lineTo(x, 56);
                    ctx.stroke();
                  }

                  // 3. Fine grid on vehicle & obstacle zone (step = 5)
                  ctx.strokeStyle = 'rgba(0, 212, 255, 0.8)';
                  ctx.lineWidth = 0.6;
                  for (let x = cx - 20; x <= cx + 20; x += 5) {
                    ctx.beginPath();
                    ctx.moveTo(x, 20);
                    ctx.lineTo(x, 46);
                    ctx.stroke();
                  }
                  for (let y = 20; y <= 46; y += 5) {
                    ctx.beginPath();
                    ctx.moveTo(cx - 20, y);
                    ctx.lineTo(cx + 20, y);
                    ctx.stroke();
                  }
                }}
              />
              <span className="absolute bottom-1 right-1 text-[8px] font-mono font-bold bg-[#09101f]/85 px-1 rounded text-emerald-400 border border-[#172742]">
                4,520 cells (-68.3%)
              </span>
            </div>
            <span className="text-[9px] text-emerald-400 font-medium mt-1">Fine on obstacles only</span>
          </div>
        </div>
      </div>
    </div>
  );
}
