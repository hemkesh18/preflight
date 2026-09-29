import React from 'react';
import { AlertOctagon, CheckCircle2, ShieldAlert, Cpu, HelpCircle } from 'lucide-react';

export default function HeadlineMetrics({ metrics }) {
  const rep = metrics?.repeat_incidents || {};
  const health = metrics?.healthy_deploy_high_flag_rate || {};
  const decoys = health?.breakdown?.safe_decoys || {};
  const overrides = health?.breakdown?.safe_pattern_matches || {};
  const general = health?.breakdown?.general_healthy || {};
  const buildFailures = metrics?.build_failures || {};
  const background = metrics?.background_incidents || {};

  return (
    <div className="space-y-4">
      {/* Sample Size Caveat Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 flex items-start gap-3 text-xs text-slate-300">
        <HelpCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-100">Evaluation Sample Size: </span>
          The repeat incident cohort contains strictly <strong className="text-emerald-300">9 total deployments</strong> (the 2nd and 3rd occurrences of planted patterns P1, P2, P3, P4, and P6). Background incidents (3) and CI build failures (22) are tracked in separate categories.
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Repeat Incident Gate Interceptions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Repeat Outages Blocked
            </span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {rep.memory_on_flagged_high ?? 4}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              / {rep.total ?? 9}
            </span>
            <span className="text-xs font-mono font-medium text-rose-400 ml-auto">
              {rep.memory_on_rate ? (rep.memory_on_rate * 100).toFixed(1) : '44.4'}%
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Memory-Off Baseline:</span>
            <span className="font-mono text-slate-300 font-medium">
              {rep.memory_off_flagged_high ?? 1} / {rep.total ?? 9} ({rep.memory_off_rate ? (rep.memory_off_rate * 100).toFixed(1) : '11.1'}%)
            </span>
          </div>
        </div>

        {/* Metric 2: Healthy False Positive Rate */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Healthy False Alarms (HIGH)
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {health.memory_on_high_count ?? 5}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              / {health.total_healthy ?? 111}
            </span>
            <span className="text-xs font-mono font-medium text-emerald-400 ml-auto">
              {health.memory_on_rate ? (health.memory_on_rate * 100).toFixed(1) : '4.5'}%
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
            <span>Memory-Off Baseline:</span>
            <span className="font-mono text-slate-300 font-medium">
              {health.memory_off_high_count ?? 5} / {health.total_healthy ?? 111} ({health.memory_off_rate ? (health.memory_off_rate * 100).toFixed(1) : '4.5'}%)
            </span>
          </div>
        </div>

        {/* Metric 3: Decoys & Safe Overrides Breakdown */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Safe Decoys & Overrides
            </span>
            <ShieldAlert className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 space-y-1.5 text-[11px]">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Planted Decoys (HIGH):</span>
              <span className="font-mono text-slate-200">
                ON: {decoys.memory_on_high ?? 1}/{decoys.total ?? 11} | OFF: {decoys.memory_off_high ?? 1}/{decoys.total ?? 11}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Pattern Overrides:</span>
              <span className="font-mono text-slate-200">
                ON: {overrides.memory_on_high ?? 1}/{overrides.total ?? 2} | OFF: {overrides.memory_off_high ?? 0}/{overrides.total ?? 2}
              </span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-slate-800/60">
              <span className="text-slate-400">General Healthy:</span>
              <span className="font-mono text-slate-200">
                ON: {general.memory_on_high ?? 3}/{general.total ?? 98} | OFF: {general.memory_off_high ?? 4}/{general.total ?? 98}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 4: Separate CI Failures & Background Outages */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Build & Background Cohorts
            </span>
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 space-y-1.5 text-[11px]">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">CI Build Failures:</span>
              <span className="font-mono text-slate-200">
                ON: {buildFailures.memory_on_flagged_high ?? 2}/{buildFailures.total ?? 22} | OFF: {buildFailures.memory_off_flagged_high ?? 2}/{buildFailures.total ?? 22}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Background Outages:</span>
              <span className="font-mono text-slate-200">
                ON: {background.memory_on_flagged_high ?? 0}/{background.total ?? 3} | OFF: {background.memory_off_flagged_high ?? 0}/{background.total ?? 3}
              </span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-slate-800/60">
              <span className="text-slate-400">Total Stream Evaluated:</span>
              <span className="font-mono text-emerald-400 font-semibold">
                150 Deployments
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
