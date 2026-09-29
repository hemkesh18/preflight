import React from 'react';
import { Table, Info } from 'lucide-react';

export default function ConfusionMatrixCard({ metrics }) {
  const on = metrics?.calibration_at_0_5?.memory_on || { tp: 8, fp: 11, tn: 100, fn: 9, precision: 0.4211, recall: 0.4706, f1: 0.4444 };
  const off = metrics?.calibration_at_0_5?.memory_off || { tp: 9, fp: 16, tn: 95, fn: 8, precision: 0.3600, recall: 0.5294, f1: 0.4286 };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Table className="w-4 h-4 text-emerald-400" />
            Confusion Matrices & Cohort Reconciliation
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            <strong>Positive Class</strong>: Production Outage / Incident (Risk &ge; 0.5) | <strong>Negative Class</strong>: Healthy Releases (Risk &lt; 0.5)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Matrix: Memory-On */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-emerald-400">Memory-On (Preflight Gate)</span>
            <span className="text-[11px] font-mono text-slate-400">F1: {on.f1} | Prec: {on.precision} | Rec: {on.recall}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
            <div className="bg-emerald-950/30 border border-emerald-800/40 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">True Positives (TP)</div>
              <div className="text-lg font-bold text-emerald-300 mt-1">{on.tp}</div>
              <div className="text-[10px] text-emerald-500/80 font-sans">Outages Intercepted</div>
            </div>
            <div className="bg-rose-950/30 border border-rose-800/40 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">False Positives (FP)</div>
              <div className="text-lg font-bold text-rose-300 mt-1">{on.fp}</div>
              <div className="text-[10px] text-rose-500/80 font-sans">Healthy Releases Flagged</div>
            </div>
            <div className="bg-amber-950/30 border border-amber-800/40 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">False Negatives (FN)</div>
              <div className="text-lg font-bold text-amber-300 mt-1">{on.fn}</div>
              <div className="text-[10px] text-amber-500/80 font-sans">Outages Missed (&lt; 0.5)</div>
            </div>
            <div className="bg-slate-900/60 border border-slate-800/60 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">True Negatives (TN)</div>
              <div className="text-lg font-bold text-slate-200 mt-1">{on.tn}</div>
              <div className="text-[10px] text-slate-400 font-sans">Healthy Passed Clean</div>
            </div>
          </div>
        </div>

        {/* Matrix: Memory-Off */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-400">Memory-Off (Control Baseline)</span>
            <span className="text-[11px] font-mono text-slate-400">F1: {off.f1} | Prec: {off.precision} | Rec: {off.recall}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
            <div className="bg-slate-900/40 border border-slate-800/60 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">True Positives (TP)</div>
              <div className="text-lg font-bold text-slate-200 mt-1">{off.tp}</div>
              <div className="text-[10px] text-slate-500 font-sans">Outages Intercepted</div>
            </div>
            <div className="bg-rose-950/20 border border-rose-900/30 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">False Positives (FP)</div>
              <div className="text-lg font-bold text-rose-400 mt-1">{off.fp}</div>
              <div className="text-[10px] text-rose-500/80 font-sans">Healthy Releases Flagged</div>
            </div>
            <div className="bg-amber-950/20 border border-amber-900/30 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">False Negatives (FN)</div>
              <div className="text-lg font-bold text-amber-400 mt-1">{off.fn}</div>
              <div className="text-[10px] text-amber-500/80 font-sans">Outages Missed (&lt; 0.5)</div>
            </div>
            <div className="bg-slate-900/40 border border-slate-800/60 rounded p-2.5">
              <div className="text-[10px] text-slate-400 font-sans">True Negatives (TN)</div>
              <div className="text-lg font-bold text-slate-300 mt-1">{off.tn}</div>
              <div className="text-[10px] text-slate-500 font-sans">Healthy Passed Clean</div>
            </div>
          </div>
        </div>
      </div>

      {/* Cohort Reconciliation Note */}
      <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3 text-[11px] text-slate-400 flex items-start gap-2">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p>
            <strong>Cohort Count Reconciliation:</strong> The 2&times;2 matrix covers <strong>128 deployments</strong> (17 production outages + 111 healthy deployments: 8 TP + 9 FN = 17; 11 FP + 100 TN = 111).
          </p>
          <p>
            The remaining <strong>22 deployments are CI build failures</strong> (e.g. glibc mismatches, syntax errors). Because build failures occur in the CI runner prior to deployment, they are evaluated separately and not merged into the production outage classification matrix.
          </p>
        </div>
      </div>
    </div>
  );
}
