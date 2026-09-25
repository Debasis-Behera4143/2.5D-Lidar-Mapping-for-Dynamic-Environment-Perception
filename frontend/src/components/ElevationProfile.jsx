/**
 * ElevationProfile.jsx
 * Elevation profile cross-section along the vehicle forward axis (X-Z / Y-Z elevation envelope).
 */

import React, { useMemo } from 'react';
import { Activity, Mountain, TrendingUp } from 'lucide-react';

export default function ElevationProfile({ points = [] }) {
  // Compute discretized elevation profile across forward distance bins
  const profileBins = useMemo(() => {
    if (!points || points.length === 0) {
      // Fallback synthetic envelope if empty
      return Array.from({ length: 20 }, (_, i) => ({
        distance: i * 2,
        minZ: -1.7 + Math.sin(i * 0.3) * 0.1,
        maxZ: -0.5 + Math.cos(i * 0.2) * 0.8,
        meanZ: -1.2 + Math.sin(i * 0.2) * 0.3,
      }));
    }

    const binSize = 2.0; // 2m distance bins forward (x in KITTI)
    const bins = {};

    for (const p of points) {
      const x = p.x || 0;
      const z = p.z || 0;
      if (x < 0 || x > 40) continue; // forward range [0, 40m]
      const binIdx = Math.floor(x / binSize);
      if (!bins[binIdx]) {
        bins[binIdx] = { distance: binIdx * binSize, minZ: z, maxZ: z, sumZ: z, count: 1 };
      } else {
        const b = bins[binIdx];
        if (z < b.minZ) b.minZ = z;
        if (z > b.maxZ) b.maxZ = z;
        b.sumZ += z;
        b.count += 1;
      }
    }

    const sorted = Object.values(bins).sort((a, b) => a.distance - b.distance);
    return sorted.map((b) => ({
      distance: b.distance,
      minZ: b.minZ,
      maxZ: b.maxZ,
      meanZ: b.sumZ / b.count,
    }));
  }, [points]);

  return (
    <div className="tech-card p-3 space-y-2.5 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
          <Mountain className="w-3.5 h-3.5 text-emerald-400" />
          <span>Forward Elevation Profile (X-Z Slice)</span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono-num">0m → 40m Forward</span>
      </div>

      {/* SVG Elevation Envelope Chart */}
      <div className="h-28 bg-[#040813] p-2 rounded border border-slate-800 flex flex-col justify-end">
        <svg className="w-full h-full overflow-visible" viewBox="0 0 400 80" preserveAspectRatio="none">
          {/* Ground baseline reference (-1.73m) */}
          <line x1="0" y1="65" x2="400" y2="65" stroke="#334155" strokeDasharray="3 3" strokeWidth="1" />
          <text x="5" y="60" fill="#64748b" fontSize="8" fontFamily="monospace">Ground Baseline (-1.7m)</text>

          {/* Elevation Fill Area */}
          {profileBins.length > 1 && (
            <>
              {/* Max Height Polygon */}
              <polygon
                points={`0,65 ${profileBins.map((b, i) => {
                  const x = (i / (profileBins.length - 1)) * 400;
                  const normZ = Math.min(80, Math.max(0, 65 - (b.maxZ + 1.7) * 15));
                  return `${x},${normZ}`;
                }).join(' ')} 400,65`}
                fill="rgba(56, 153, 56, 0.15)"
                stroke="#389938"
                strokeWidth="1.5"
              />

              {/* Mean Height Line */}
              <polyline
                points={profileBins.map((b, i) => {
                  const x = (i / (profileBins.length - 1)) * 400;
                  const normZ = Math.min(80, Math.max(0, 65 - (b.meanZ + 1.7) * 15));
                  return `${x},${normZ}`;
                }).join(' ')}
                fill="none"
                stroke="#00d4ff"
                strokeWidth="2"
              />
            </>
          )}
        </svg>

        {/* Legend */}
        <div className="flex items-center justify-between text-[9px] font-mono-num text-slate-400 mt-1 pt-1 border-t border-slate-900">
          <span className="flex items-center gap-1">
            <span className="w-2 h-0.5 bg-cyan-400 inline-block" />
            <span>Mean Elevation (Z)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-emerald-700/40 border border-emerald-500 inline-block" />
            <span>Max Height Envelope</span>
          </span>
          <span>Forward Range (40m)</span>
        </div>
      </div>
    </div>
  );
}
