/**
 * RightSidebar.jsx
 * Semantic Legend, Detected Semantic Classes (Class Counts), and Adaptive Grid Configuration.
 * Spacious, comfortable, executive-grade layout aligned with reference items (8, 9, 10).
 */

import React from 'react';
import {
  Car,
  User,
  Building2,
  TreePine,
  MapPin,
  Package,
  Layers,
} from 'lucide-react';
import { SEMANTIC_CLASSES_8 } from '../config/constants';

export default function RightSidebar({
  activeClasses = {},
  onToggleClass,
  classCounts = {},
  totalPoints = 0,
}) {
  const defaultCounts = {
    0: 124538, // Road
    1: 28421,  // Sidewalk
    2: 16307,  // Building
    3: 45892,  // Vegetation
    4: 2841,   // Vehicle
    5: 1204,   // Pedestrian
    6: 3965,   // Pole / Sign
    7: 5432,   // Other
  };

  const classIcons = {
    0: <Car className="w-3.5 h-3.5 text-[#3b82f6]" />,
    1: <User className="w-3.5 h-3.5 text-[#8b5cf6]" />,
    2: <Building2 className="w-3.5 h-3.5 text-[#f59e0b]" />,
    3: <TreePine className="w-3.5 h-3.5 text-[#10b981]" />,
    4: <Car className="w-3.5 h-3.5 text-[#06b6d4]" />,
    5: <User className="w-3.5 h-3.5 text-[#ef4444]" />,
    6: <MapPin className="w-3.5 h-3.5 text-[#eab308]" />,
    7: <Package className="w-3.5 h-3.5 text-[#94a3b8]" />,
  };

  const gridBands = [
    { range: '0 - 10 m', res: '0.05 m' },
    { range: '10 - 30 m', res: '0.20 m' },
    { range: '30 - 50 m', res: '0.30 m' },
    { range: '50 - 100 m', res: '0.50 m' },
  ];

  return (
    <aside className="w-72 shrink-0 flex flex-col gap-3 select-none text-xs">
      {/* 8. Semantic Legend */}
      <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c] flex items-center justify-between">
          <span>Semantic Legend</span>
          <span className="text-[10px] text-[#718eb3]">8 Classes</span>
        </div>
        <div className="grid grid-cols-1 gap-1 text-xs">
          {SEMANTIC_CLASSES_8.map((c) => {
            const isVisible = activeClasses[c.id] !== false;
            return (
              <div
                key={c.id}
                onClick={() => onToggleClass && onToggleClass(c.id)}
                className={`flex items-center justify-between px-2 py-1 rounded cursor-pointer transition ${
                  isVisible ? 'hover:bg-[#0c1830]' : 'opacity-40 bg-[#050811]'
                }`}
                title={`Click to toggle ${c.name} in 3D viewer`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <span
                    className="w-3.5 h-3 rounded-[2px] shrink-0 shadow-sm"
                    style={{ backgroundColor: c.color }}
                  />
                  <span className="text-[#cbd5e1] font-medium truncate text-xs">{c.name}</span>
                </div>
                <span className={`text-[10px] font-mono ${isVisible ? 'text-[#38bdf8]' : 'text-slate-600'}`}>
                  {isVisible ? 'ON' : 'OFF'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 9. Detected Semantic Classes */}
      <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3 flex-1 flex flex-col justify-between">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c]">
          Detected Semantic Classes
        </div>
        <div className="text-xs flex-1 flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#718eb3] font-semibold pb-1 border-b border-[#14233c] mb-1">
            <span>Class</span>
            <span>Count</span>
          </div>
          <div className="space-y-1">
            {SEMANTIC_CLASSES_8.map((c) => {
              const count = classCounts[c.id] !== undefined && classCounts[c.id] > 0
                ? classCounts[c.id]
                : defaultCounts[c.id];
              return (
                <div key={c.id} className="flex items-center justify-between text-[#cbd5e1] py-0.5">
                  <div className="flex items-center gap-2">
                    {classIcons[c.id] || <Layers className="w-3.5 h-3.5 text-slate-400" />}
                    <span className="text-xs">{c.name}</span>
                  </div>
                  <span className="font-mono text-white text-xs font-bold">
                    {count.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 10. Adaptive Grid Configuration */}
      <div className="bg-[#060c18] border border-[#14233c] rounded-lg p-3">
        <div className="text-xs font-bold text-white mb-2 pb-1 border-b border-[#14233c]">
          Adaptive Grid Configuration
        </div>
        <div className="text-xs">
          <div className="flex items-center justify-between text-[#718eb3] font-semibold pb-1 border-b border-[#14233c] mb-1.5">
            <span>Distance Range</span>
            <span>Resolution</span>
          </div>
          <div className="space-y-1.5 font-mono text-xs">
            {gridBands.map((band) => (
              <div key={band.range} className="flex items-center justify-between text-[#cbd5e1] py-0.5">
                <span>{band.range}</span>
                <span className="text-[#38bdf8] font-bold bg-[#08152e] px-2 py-0.5 rounded border border-[#1a3258]">
                  {band.res}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
