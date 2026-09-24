import React from 'react';
import { Target, Shield, Car, Trees, Grid, Map } from 'lucide-react';

export default function FooterBar() {
  return (
    <footer className="w-full bg-[#09101f] border border-[#172742] rounded-md px-3 py-2 flex flex-wrap items-center justify-between text-xs text-[#94a3b8] gap-3 shadow-md">
      {/* Left Explanatory Block */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-full bg-[#00d4ff]/10 border border-[#00d4ff]/30 flex items-center justify-center text-[#00d4ff] shrink-0">
          <Target className="w-4 h-4" />
        </div>
        <div>
          <div className="font-bold text-white text-xs">What This Dashboard Shows</div>
          <div className="text-[10px] text-[#94a3b8] leading-tight">
            A real-time view of the LiDAR scene, semantic understanding, adaptive 2.5D mapping and system performance.
          </div>
        </div>
      </div>

      {/* Right Semantic Tag Properties */}
      <div className="flex items-center gap-4 text-[11px]">
        {/* Left Wall */}
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-[#ef4444]" />
          <div>
            <span className="font-bold text-white">Left Wall</span>{' '}
            <span className="text-[10px] text-[#ef4444]">(Non-drivable)</span>
          </div>
        </div>

        {/* Front Vehicle */}
        <div className="flex items-center gap-1.5">
          <Car className="w-3.5 h-3.5 text-[#d946ef]" />
          <div>
            <span className="font-bold text-white">Front Vehicle</span>{' '}
            <span className="text-[10px] text-[#d946ef]">(Dynamic)</span>
          </div>
        </div>

        {/* Right Tree */}
        <div className="flex items-center gap-1.5">
          <Trees className="w-3.5 h-3.5 text-[#10b981]" />
          <div>
            <span className="font-bold text-white">Right Tree</span>{' '}
            <span className="text-[10px] text-[#10b981]">(Static)</span>
          </div>
        </div>

        {/* Grid Resolution */}
        <div className="flex items-center gap-1.5">
          <Grid className="w-3.5 h-3.5 text-[#00d4ff]" />
          <div>
            <span className="font-bold text-white">Grid Resolution</span>{' '}
            <span className="text-[10px] text-[#00d4ff] font-mono">(5 cm / 10 cm / 25 cm / 50 cm)</span>
          </div>
        </div>

        {/* Map Type */}
        <div className="flex items-center gap-1.5">
          <Map className="w-3.5 h-3.5 text-[#a855f7]" />
          <div>
            <span className="font-bold text-white">Map Type</span>{' '}
            <span className="text-[10px] text-[#a855f7]">Semantic 2.5D Elevation</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
