/**
 * SemanticLegend.jsx
 * Right side Semantic Legend matching reference screenshot and Part 19 requirements.
 * Shows exactly the 8 classes with color, eye toggle, and real point counts.
 */

import React from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { SEMANTIC_CLASSES_8 } from '../config/constants';

export default function SemanticLegend({
  activeClasses = {},
  onToggleClass,
  classCounts = {},
  totalPoints = 0,
}) {
  return (
    <div className="bg-[#071123] border border-[#162744] rounded-lg p-2.5 flex-1 select-none flex flex-col">
      <div className="text-xs font-bold text-white mb-2 tracking-tight flex items-center justify-between">
        <span>Semantic Legend</span>
        <span className="text-[9px] font-mono text-[#7896bf]">8 Classes</span>
      </div>

      <div className="space-y-1.5 text-[11px] overflow-y-auto flex-1">
        {SEMANTIC_CLASSES_8.map((c) => {
          const isVisible = activeClasses[c.id] !== false;
          const count = classCounts[c.id] || 0;
          const pct = totalPoints > 0 ? ((count / totalPoints) * 100).toFixed(1) : '0';

          return (
            <div
              key={c.id}
              className={`flex items-center justify-between p-1 rounded transition ${
                isVisible ? 'bg-[#09152b] hover:bg-[#0e2142]' : 'bg-[#060c18] opacity-50'
              }`}
            >
              {/* Color & Label */}
              <div
                className="flex items-center gap-2 cursor-pointer flex-1 min-w-0"
                onClick={() => onToggleClass && onToggleClass(c.id)}
              >
                <span
                  className="w-3 h-3 rounded-sm shrink-0 shadow-sm"
                  style={{ backgroundColor: c.color }}
                />
                <span className="truncate text-[#b0c4de] text-[10.5px]">{c.name}</span>
              </div>

              {/* Point Count & Eye Toggle */}
              <div className="flex items-center gap-2 shrink-0 font-mono text-[10px]">
                <span className="text-[#84a3c7] font-semibold">
                  {count > 0 ? count.toLocaleString() : '0'} <span className="text-[8px] text-[#506c8f]">pts</span>
                </span>
                <button
                  onClick={() => onToggleClass && onToggleClass(c.id)}
                  className={`p-0.5 rounded transition ${
                    isVisible ? 'text-cyan-400 hover:text-cyan-300' : 'text-slate-600 hover:text-slate-400'
                  }`}
                  title={isVisible ? `Hide ${c.name}` : `Show ${c.name}`}
                >
                  {isVisible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
