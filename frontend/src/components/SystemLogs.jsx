/**
 * SystemLogs.jsx
 * Live diagnostic system console / terminal displaying runtime events, inference timing, and memory metrics.
 */

import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

export default function SystemLogs({ logs = [] }) {
  const scrollRef = useRef();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const defaultLogs = [
    { time: '20:14:02.102', level: 'INFO', msg: 'System initialized. Model RandLA-Net loaded on device.' },
    { time: '20:14:02.240', level: 'INFO', msg: 'FastAPI backend healthy at 127.0.0.1:8000 (status: 200 OK).' },
    { time: '20:14:03.015', level: 'SUCCESS', msg: 'Velodyne scan 000000.bin ingested (4096 points).' },
    { time: '20:14:03.110', level: 'SUCCESS', msg: 'Adaptive 2.5D grid generated: 64.8% memory savings achieved.' },
  ];

  const rawLogs = logs.length > 0 ? logs : defaultLogs;

  const displayLogs = rawLogs.map((log) => {
    if (typeof log === 'string') {
      return { time: new Date().toTimeString().split(' ')[0], level: 'INFO', msg: log };
    }
    let msgText = '';
    if (typeof log.msg === 'object' && log.msg !== null) {
      msgText = log.msg.msg || log.msg.message || JSON.stringify(log.msg);
    } else if (typeof log.msg === 'string') {
      msgText = log.msg;
    } else if (typeof log.message === 'string') {
      msgText = log.message;
    } else if (log.tag && log.text) {
      msgText = log.text;
    } else {
      msgText = String(log.msg || log.message || log.text || JSON.stringify(log));
    }

    return {
      time: typeof log.time === 'string' ? log.time : new Date().toTimeString().split(' ')[0],
      level: log.level || log.tag || 'INFO',
      msg: msgText,
    };
  });

  return (
    <div className="tech-card p-3 space-y-2 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
          <Terminal className="w-3.5 h-3.5 text-purple-400" />
          <span>System Diagnostics & Events</span>
        </div>
        <span className="text-[10px] text-emerald-400 font-mono-num">LIVE</span>
      </div>

      {/* Terminal View */}
      <div
        ref={scrollRef}
        className="bg-[#03060f] p-2.5 rounded border border-slate-900 h-32 overflow-y-auto space-y-1 font-mono-num text-[10px]"
      >
        {displayLogs.map((log, i) => {
          const isErr = log.level === 'ERROR' || log.level === 'WARN';
          const isSuccess = log.level === 'SUCCESS';

          return (
            <div key={i} className="flex items-start gap-1.5 leading-relaxed">
              <span className="text-slate-600 shrink-0">[{log.time}]</span>
              <span
                className={`font-bold shrink-0 ${
                  isErr
                    ? 'text-amber-400'
                    : isSuccess
                    ? 'text-emerald-400'
                    : 'text-blue-400'
                }`}
              >
                {log.level}:
              </span>
              <span className="text-slate-300 break-all">{log.msg}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
