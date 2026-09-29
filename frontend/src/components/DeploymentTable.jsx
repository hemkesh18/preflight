import React, { useState } from 'react';
import { Search, Filter, ArrowUpDown } from 'lucide-react';

export default function DeploymentTable({ records, onSelectDeploy, selectedDeployId }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const filtered = (records || []).filter((r) => {
    const matchesSearch =
      r.deploy_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.change_type?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      categoryFilter === 'ALL' ||
      (categoryFilter === 'REPEAT' && r.category === 'repeat_incident') ||
      (categoryFilter === 'NOVEL' && r.category === 'novel_incident') ||
      (categoryFilter === 'HEALTHY' && r.category?.includes('healthy')) ||
      (categoryFilter === 'BUILD' && r.category === 'build_failure');

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Full Deployment Evaluation Stream (150 Deployments)</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Click any deployment to inspect its preflight gate decision, memory citations, and baseline comparison
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search deploy, service..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-44 sm:w-56"
            />
          </div>

          {/* Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Cohorts (150)</option>
            <option value="REPEAT">Repeat Outages (9)</option>
            <option value="NOVEL">Novel Outages (5)</option>
            <option value="HEALTHY">Healthy Deploys (111)</option>
            <option value="BUILD">Build Failures (22)</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-800/80 rounded-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Step</th>
              <th className="py-2.5 px-3">Deploy ID</th>
              <th className="py-2.5 px-3">Service</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Ground Truth</th>
              <th className="py-2.5 px-3 text-right">MEM-ON Score</th>
              <th className="py-2.5 px-3 text-right">MEM-OFF Score</th>
              <th className="py-2.5 px-3 text-center">Citations</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
            {filtered.map((r) => {
              const isSelected = r.deploy_id === selectedDeployId;
              const memOn = r.memory_on || {};
              const memOff = r.memory_off || {};
              return (
                <tr
                  key={r.deploy_id}
                  onClick={() => onSelectDeploy && onSelectDeploy(r.deploy_id)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-emerald-950/40 text-emerald-200'
                      : 'hover:bg-slate-800/40 text-slate-300'
                  }`}
                >
                  <td className="py-2 px-3 text-slate-500">{r.step}</td>
                  <td className="py-2 px-3 font-bold text-slate-100">{r.deploy_id}</td>
                  <td className="py-2 px-3 font-sans text-slate-300">{r.service}</td>
                  <td className="py-2 px-3 text-slate-400">{r.change_type}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-sans ${
                        r.category === 'repeat_incident'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : r.category === 'novel_incident'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : r.category === 'build_failure'
                          ? 'bg-blue-500/20 text-blue-300'
                          : 'bg-emerald-500/10 text-emerald-400'
                      }`}
                    >
                      {r.category}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-bold">
                    <span
                      className={
                        memOn.risk_level === 'HIGH'
                          ? 'text-rose-400'
                          : memOn.risk_level === 'MEDIUM'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }
                    >
                      {(memOn.risk_score || 0).toFixed(2)} ({memOn.risk_level})
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right text-slate-400">
                    {(memOff.risk_score || 0).toFixed(2)} ({memOff.risk_level})
                  </td>
                  <td className="py-2 px-3 text-center text-emerald-400">
                    {memOn.grounded_citation_count > 0 ? (
                      <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/60">
                        {memOn.grounded_citation_count}
                      </span>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
