import React, { useState } from 'react';
import { GitPullRequest, ShieldAlert, CheckCircle, XCircle, AlertTriangle, BookOpen, Link2 } from 'lucide-react';

export default function GateSimulator({ records, onSelectDeploy }) {
  // Preset key illustrative deployments
  const PRESETS = [
    { id: 'dep-131', label: 'dep-131: Repeat Friday Payments Outage (P1)', badge: 'Repeat Outage' },
    { id: 'dep-111', label: 'dep-111: First Friday Payments Outage (Novel)', badge: 'Novel Outage' },
    { id: 'dep-101', label: 'dep-101: Early Safe Payments CPU Increase', badge: 'Safe Clean' },
    { id: 'dep-223', label: 'dep-223: Safe Friday Payments Canary Override', badge: 'Safe Override' },
    { id: 'dep-164', label: 'dep-164: Repeat Ledger Unbackfilled Migration (P2)', badge: 'Repeat Outage' },
  ];

  const [selectedId, setSelectedId] = useState('dep-131');
  const currentRecord = records?.find((r) => r.deploy_id === selectedId) || records?.[0] || {};
  const memOn = currentRecord?.memory_on || {};
  const memOff = currentRecord?.memory_off || {};

  const handleSelect = (id) => {
    setSelectedId(id);
    if (onSelectDeploy) onSelectDeploy(id);
  };

  const getActionBadge = (level, score) => {
    if (level === 'HIGH' || score >= 0.6) {
      return (
        <span className="px-2.5 py-1 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold text-xs flex items-center gap-1.5">
          <XCircle className="w-3.5 h-3.5" /> BLOCK (Exit 1)
        </span>
      );
    }
    if (level === 'MEDIUM' || score >= 0.35) {
      return (
        <span className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold text-xs flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" /> WARN (Exit 0)
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold text-xs flex items-center gap-1.5">
        <CheckCircle className="w-3.5 h-3.5" /> PASS (Exit 0)
      </span>
    );
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <GitPullRequest className="w-4 h-4 text-emerald-400" />
            Interactive CI/CD Gate Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Compare live gate evaluation: Memory-On with persistent Hindsight evidence vs Memory-Off baseline
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex flex-wrap gap-1.5">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelect(p.id)}
              className={`text-[11px] px-2.5 py-1 rounded-lg border font-medium transition-colors ${
                selectedId === p.id
                  ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {p.id} ({p.badge})
            </button>
          ))}
        </div>
      </div>

      {/* Selected Deploy Header Bar */}
      <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-slate-100">{currentRecord.deploy_id}</span>
            <span className="text-slate-400">&bull;</span>
            <span className="text-slate-300 font-medium">{currentRecord.service}</span>
            <span className="text-slate-500 font-mono">({currentRecord.change_type})</span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono">Timestamp: {currentRecord.timestamp}</p>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-slate-400">Ground Truth Category:</span>
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 font-mono text-emerald-300">
            {currentRecord.category}
          </span>
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Arm 1: Memory-On */}
        <div className="bg-slate-950/60 border border-emerald-900/40 rounded-lg p-4 space-y-4 relative">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" /> Memory-On (Preflight Gate)
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                Model: {memOn.model_used || 'openai/gpt-oss-120b'}
              </p>
            </div>
            {getActionBadge(memOn.risk_level, memOn.risk_score)}
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
              <span className="text-[10px] text-slate-400">Assessed Risk Score</span>
              <div className="text-base font-bold font-mono text-white mt-0.5">
                {(memOn.risk_score || 0).toFixed(2)}{' '}
                <span className="text-xs font-normal text-slate-400">({memOn.risk_level})</span>
              </div>
            </div>
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
              <span className="text-[10px] text-slate-400">Grounded Citations</span>
              <div className="text-base font-bold font-mono text-emerald-400 mt-0.5 flex items-center gap-1">
                <Link2 className="w-3.5 h-3.5" />
                {memOn.grounded_citation_count || 0} valid IDs
              </div>
            </div>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-300">Predicted Failure Mode:</span>
            <p className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded mt-1 border border-slate-800">
              {memOn.predicted_failure_mode || 'None anticipated'}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-300">Grounded Reasons:</span>
            <div className="space-y-1.5 mt-1">
              {(memOn.reasons || []).map((r, i) => (
                <div key={i} className="text-xs text-slate-300 bg-slate-900/40 p-2 rounded border border-slate-800/60">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-300 font-bold">
                      {r.severity}
                    </span>
                    <span>{r.summary}</span>
                  </div>
                  {r.memory_ids?.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1 text-[10px] font-mono text-emerald-400">
                      {r.memory_ids.map((mid) => (
                        <span key={mid} className="px-1.5 py-0.5 bg-emerald-950/60 border border-emerald-800/60 rounded">
                          id:{mid.slice(0, 8)}...
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {memOn.what_worked_before && (
            <div className="bg-emerald-950/20 border border-emerald-800/40 rounded p-2.5 text-xs text-emerald-200">
              <span className="font-semibold text-[11px] text-emerald-300 flex items-center gap-1">
                <BookOpen className="w-3.5 h-3.5" /> What Worked Before (Runbook Precedent):
              </span>
              <p className="mt-1 text-[11px] leading-relaxed">{memOn.what_worked_before}</p>
            </div>
          )}
        </div>

        {/* Arm 2: Memory-Off */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4 space-y-4 relative">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <span className="text-xs font-bold text-slate-400">Memory-Off (Control Baseline)</span>
              <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                Model: {memOff.model_used || 'openai/gpt-oss-120b'}
              </p>
            </div>
            {getActionBadge(memOff.risk_level, memOff.risk_score)}
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
              <span className="text-[10px] text-slate-400">Assessed Risk Score</span>
              <div className="text-base font-bold font-mono text-white mt-0.5">
                {(memOff.risk_score || 0).toFixed(2)}{' '}
                <span className="text-xs font-normal text-slate-400">({memOff.risk_level})</span>
              </div>
            </div>
            <div className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60">
              <span className="text-[10px] text-slate-400">Citations</span>
              <div className="text-base font-bold font-mono text-slate-400 mt-0.5">
                0 (No Memory Bank)
              </div>
            </div>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-300">Predicted Failure Mode:</span>
            <p className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded mt-1 border border-slate-800">
              {memOff.predicted_failure_mode || 'None anticipated'}
            </p>
          </div>

          <div>
            <span className="text-[11px] font-semibold text-slate-300">Heuristic Reasons:</span>
            <div className="space-y-1.5 mt-1">
              {(memOff.reasons || []).map((r, i) => (
                <div key={i} className="text-xs text-slate-300 bg-slate-900/40 p-2 rounded border border-slate-800/60">
                  <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-slate-700 text-slate-300 font-bold mr-1.5">
                    {r.severity}
                  </span>
                  <span>{r.summary}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800/60 rounded p-2.5 text-xs text-slate-400">
            <span className="text-[11px] font-semibold text-slate-400">Runbook Remediation:</span>
            <p className="mt-1 text-[11px]">
              Unavailable without persistent incident memory bank.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
