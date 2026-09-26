/**
 * LowerAnalytics.jsx
 * Bottom analytical row aligned with reference layout:
 * 14. Performance Metrics (4 circular gauges: mIoU, FPS, Latency, Memory)
 * 15. Uniform vs Adaptive Comparison (Clean, spacious text table)
 * 16. System Log (Live terminal placed at the bottom corner)
 */

import React from 'react';

/**
 * 14. Performance Metrics with 4 Circular Gauges
 */
export function PerformanceMetricsGauges({
  miou = '-- %',
  fps = '12.4',
  latencyMs = '82 ms',
  memory = '640 MB',
}) {
  const metrics = [
    {
      label: 'mIoU',
      value: miou,
      color: '#06b6d4',
      ringPct: 75,
    },
    {
      label: 'FPS',
      value: fps,
      color: '#3b82f6',
      ringPct: 62,
    },
    {
      label: 'Latency',
      value: latencyMs,
      color: '#8b5cf6',
      ringPct: 40,
    },
    {
      label: 'Memory',
      value: memory,
      color: '#f43f5e',
      ringPct: 55,
    },
  ];

  return (
    <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c] flex items-center justify-between">
        <span>Performance Metrics</span>
        <span className="text-[10px] font-mono text-[#38bdf8]">Real-time Telemetry</span>
      </div>

      <div className="flex-1 grid grid-cols-4 gap-3 items-center justify-items-center">
        {metrics.map((m) => {
          const radius = 26;
          const circumference = 2 * Math.PI * radius;
          const strokeDashoffset = circumference - (m.ringPct / 100) * circumference;

          return (
            <div key={m.label} className="flex flex-col items-center">
              <span className="text-[11px] text-[#8da8cf] mb-1 font-semibold">{m.label}</span>
              <div className="relative w-16 h-16 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  {/* Background Track Ring */}
                  <circle
                    cx="32"
                    cy="32"
                    r={radius}
                    stroke="#0f1f38"
                    strokeWidth="4"
                    fill="transparent"
                  />
                  {/* Glowing Colored Ring */}
                  <circle
                    cx="32"
                    cy="32"
                    r={radius}
                    stroke={m.color}
                    strokeWidth="4"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    fill="transparent"
                  />
                </svg>
                <span className="absolute text-xs font-bold font-mono text-white">
                  {m.value}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * 15. Uniform vs Adaptive Comparison Table (Pure clean text table)
 */
export function GridComparisonPanel({
  uniformCells = 245820,
  adaptiveCells = 91430,
}) {
  const reductionPct = uniformCells > 0
    ? (((uniformCells - adaptiveCells) / uniformCells) * 100).toFixed(1)
    : '62.8';

  const rows = [
    {
      metric: 'Number of Cells',
      uniform: uniformCells ? uniformCells.toLocaleString() : '245,820',
      adaptive: adaptiveCells ? adaptiveCells.toLocaleString() : '91,430',
      reduction: `↓ ${reductionPct}%`,
      reductionColor: 'text-[#10b981]',
    },
    {
      metric: 'Memory Usage',
      uniform: '512 MB',
      adaptive: '206 MB',
      reduction: '↓ 59.8%',
      reductionColor: 'text-[#10b981]',
    },
    {
      metric: 'Mapping Time',
      uniform: '120 ms',
      adaptive: '48 ms',
      reduction: '↓ 60.0%',
      reductionColor: 'text-[#10b981]',
    },
    {
      metric: 'Near-field mIoU',
      uniform: '82.1%',
      adaptive: '81.4%',
      reduction: '-0.7%',
      reductionColor: 'text-[#94a3b8]',
    },
  ];

  return (
    <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3 flex-[1.4] flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c] flex items-center justify-between">
        <span>Uniform vs Adaptive Comparison</span>
        <span className="text-[10px] font-mono text-[#10b981] font-bold">Spatial Savings</span>
      </div>

      <div className="flex-1 flex flex-col justify-center">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="text-[#718eb3] border-b border-[#14233c]">
              <th className="pb-1.5 font-semibold">Metric</th>
              <th className="pb-1.5 font-semibold">Uniform Grid</th>
              <th className="pb-1.5 font-semibold">Adaptive Grid</th>
              <th className="pb-1.5 font-semibold">Reduction</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#0f1d33]">
            {rows.map((r) => (
              <tr key={r.metric} className="text-[#cbd5e1]">
                <td className="py-1.5 text-slate-300 font-sans text-xs">{r.metric}</td>
                <td className="py-1.5 text-slate-200">{r.uniform}</td>
                <td className="py-1.5 text-slate-200">{r.adaptive}</td>
                <td className={`py-1.5 font-bold ${r.reductionColor}`}>
                  {r.reduction}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * 16. System Log placed at bottom corner
 */
export function SystemLogsPanel({ logs = [] }) {
  const defaultLogs = [
    { time: '14:32:10', text: 'Loaded frame 000000' },
    { time: '14:32:11', text: 'Preprocessing completed (154,320 points)' },
    { time: '14:32:12', text: 'Inference completed (82 ms)' },
    { time: '14:32:12', text: 'Adaptive grid generated (48 ms)' },
    { time: '14:32:13', text: '2.5D maps created' },
    { time: '14:32:14', text: 'Visualization updated' },
    { time: '14:32:14', text: 'Processing complete' },
  ];

  const displayLogs = logs && logs.length > 0 ? logs : defaultLogs;

  return (
    <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3 flex-1 flex flex-col select-none">
      <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c] flex items-center justify-between">
        <span>System Log</span>
        <span className="text-[10px] font-mono text-cyan-400">Live Stream</span>
      </div>

      <div className="flex-1 bg-[#030712] border border-[#14233c] rounded p-2.5 overflow-y-auto font-mono text-[10.5px] space-y-1">
        {displayLogs.map((l, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-[#51749c]">[{l.time || '14:32:10'}]</span>
            <span className="text-[#93b2d6]">{l.text || l.msg || l}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
