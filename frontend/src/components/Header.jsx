import React from 'react';
import { ShieldCheck, Database, Radio, AlertTriangle } from 'lucide-react';

export default function Header({ metadata, demoMode, fallbackBanner }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      {fallbackBanner && (
        <div className="bg-amber-950/80 border-b border-amber-800/80 px-4 py-2 text-xs text-amber-200 flex items-center justify-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>{fallbackBanner}</span>
        </div>
      )}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-950/40">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white font-['Plus_Jakarta_Sans']">
                PREFLIGHT
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                CI/CD Release Gate
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Persistent Memory-Grounded Deployment Safety for Kestrel Pay
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">Memory Bank:</span>
            <span className="font-mono text-slate-200 font-medium">
              {metadata?.bank_id || 'kestrel-pay'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs">
            <Radio className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
            <span className="text-slate-400">Mode:</span>
            <span className="uppercase font-semibold text-blue-300">
              {demoMode || metadata?.primary_model?.includes('gpt') ? 'cached' : 'live'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
