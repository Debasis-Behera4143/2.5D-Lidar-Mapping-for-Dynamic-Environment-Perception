import React from 'react';
import { DISPLAY_TAXONOMY, RESOLUTION_BANDS } from '../config/constants';
import { Car, User, Bike, MapPin, Package, Shield } from 'lucide-react';

export default function RightPanels({ sceneObjects = {} }) {
  const objectIcons = {
    Vehicle: <Car className="w-3.5 h-3.5 text-[#d946ef]" />,
    Pedestrian: <User className="w-3.5 h-3.5 text-[#eab308]" />,
    Motorcycle: <Bike className="w-3.5 h-3.5 text-[#38bdf8]" />,
    Bicycle: <Bike className="w-3.5 h-3.5 text-[#10b981]" />,
    'Static (Pole/Sign)': <MapPin className="w-3.5 h-3.5 text-[#06b6d4]" />,
    Others: <Package className="w-3.5 h-3.5 text-[#64748b]" />,
  };

  return (
    <div className="flex flex-col gap-2 w-full">
      {/* 1. Semantic Legend Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#172742] flex items-center justify-between">
          <span>Semantic Legend</span>
          <span className="text-[10px] text-[#00d4ff] bg-[#00d4ff]/10 px-1.5 py-0.5 rounded border border-[#00d4ff]/30">
            10 Classes
          </span>
        </div>
        <div className="grid grid-cols-1 gap-1 text-[11px]">
          {DISPLAY_TAXONOMY.map((item) => (
            <div key={item.id} className="flex items-center justify-between py-0.5 px-1 rounded hover:bg-[#132035]/60 transition">
              <div className="flex items-center gap-2">
                <span
                  className="w-3.5 h-2.5 rounded-[2px] shadow-sm shrink-0"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-[#f1f5f9] font-medium text-[11px] truncate max-w-[130px]">{item.name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Object Detection (Count) Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#172742] flex items-center justify-between">
          <span>Object Detection (Count)</span>
          <span className="text-[9px] text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded border border-amber-400/30">
            DYNAMIC + STATIC
          </span>
        </div>
        <div className="space-y-1 text-[11px]">
          {Object.entries(sceneObjects).map(([name, count]) => (
            <div key={name} className="flex items-center justify-between py-0.5 px-1 rounded hover:bg-[#132035]/50">
              <div className="flex items-center gap-1.5 text-[#cbd5e1]">
                {objectIcons[name] || <Shield className="w-3.5 h-3.5 text-[#64748b]" />}
                <span>{name}</span>
              </div>
              <span className="font-mono font-bold text-white bg-[#0d172a] px-1.5 py-0.2 rounded border border-[#1e293b]">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Adaptive Grid Resolution Card */}
      <div className="bg-[#09101f] border border-[#172742] rounded-md p-2.5 shadow-md">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#172742] flex items-center justify-between">
          <span>Adaptive Grid Resolution</span>
          <span className="text-[9px] text-[#38bdf8] bg-[#38bdf8]/10 px-1.5 py-0.5 rounded border border-[#38bdf8]/30">
            4 BANDS
          </span>
        </div>
        <div className="space-y-1.5">
          {RESOLUTION_BANDS.map((band) => (
            <div
              key={band.range}
              className="flex items-center justify-between px-2 py-1 rounded border text-[11px] font-mono font-semibold"
              style={{
                backgroundColor: band.bg,
                borderColor: band.color,
                color: band.color,
              }}
            >
              <span>{band.range}</span>
              <span className="font-bold">({band.res})</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
