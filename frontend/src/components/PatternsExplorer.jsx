import React, { useState, useEffect } from 'react';
import { Layers, ShieldCheck, AlertCircle, Database, CheckCircle2 } from 'lucide-react';

export default function PatternsExplorer({ patternsData }) {
  const [data, setData] = useState(patternsData);
  const [loading, setLoading] = useState(!patternsData);

  useEffect(() => {
    if (patternsData) {
      setData(patternsData);
      setLoading(false);
      return;
    }
    // Fallback: fetch directly from endpoint if not passed as prop
    async function loadPatterns() {
      try {
        const res = await fetch('/api/patterns');
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error('Failed to load patterns from /api/patterns:', err);
      } finally {
        setLoading(false);
      }
    }
    loadPatterns();
  }, [patternsData]);

  if (loading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        Loading synthesized failure patterns from Hindsight reflect...
      </div>
    );
  }

  const summary = data?.patterns_summary || 'No reflection patterns loaded from Hindsight.';
  const evidenceIds = data?.evidence_memory_ids || [];
  const bankId = data?.bank_id || 'kestrel-pay';
  const status = data?.status || 'active';

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      {/* Header bar with authentic bank metadata */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Synthesized Recurring Failure Patterns (Hindsight Reflect)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Operational risk patterns consolidated across deployment memories via Hindsight Cloud reflection
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded bg-slate-800/90 text-slate-300 font-mono text-[11px] border border-slate-700/60 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            bank: {bankId}
          </span>
          <span className="px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 font-mono text-[11px] border border-emerald-500/20 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            status: {status}
          </span>
          <span className="px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 font-mono text-[11px] border border-indigo-500/20">
            {evidenceIds.length} citations
          </span>
        </div>
      </div>

      {/* Verbatim synthesized output rendered with typography */}
      <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-5 text-xs text-slate-300 leading-relaxed font-sans space-y-4 max-h-[500px] overflow-y-auto">
        <div className="prose prose-invert prose-xs max-w-none space-y-3">
          {summary.split('\n\n').map((paragraph, idx) => {
            const trimmed = paragraph.trim();
            if (trimmed.startsWith('## ')) {
              return (
                <h3 key={idx} className="text-sm font-bold text-white border-b border-slate-800 pb-1.5 pt-2">
                  {trimmed.replace('## ', '')}
                </h3>
              );
            }
            if (trimmed.startsWith('### ')) {
              return (
                <h4 key={idx} className="text-xs font-bold text-emerald-400 pt-2 uppercase tracking-wider">
                  {trimmed.replace('### ', '')}
                </h4>
              );
            }
            if (trimmed.includes('| Service |') || trimmed.startsWith('|')) {
              const rows = trimmed.split('\n').filter(r => !r.includes(':---'));
              return (
                <div key={idx} className="overflow-x-auto my-2 border border-slate-800 rounded">
                  <table className="w-full text-left border-collapse text-[11px]">
                    <tbody>
                      {rows.map((row, rIdx) => {
                        const cells = row.split('|').map(c => c.trim()).filter(Boolean);
                        if (cells.length === 0) return null;
                        const isHeader = rIdx === 0;
                        return (
                          <tr key={rIdx} className={isHeader ? 'bg-slate-800/70 text-slate-200 font-semibold' : 'border-t border-slate-800/60 hover:bg-slate-900/40'}>
                            {cells.map((cell, cIdx) => (
                              <td key={cIdx} className="px-3 py-1.5 font-mono">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              );
            }
            if (trimmed.startsWith('*   ') || trimmed.startsWith('* ')) {
              const bullets = trimmed.split('\n*').map(b => b.replace(/^\*\s*/, '').trim()).filter(Boolean);
              return (
                <ul key={idx} className="space-y-1.5 pl-4 list-disc list-outside text-slate-300">
                  {bullets.map((b, bIdx) => (
                    <li key={bIdx} className="leading-normal">
                      {b}
                    </li>
                  ))}
                </ul>
              );
            }
            return (
              <p key={idx} className="text-slate-300 leading-relaxed">
                {trimmed}
              </p>
            );
          })}
        </div>
      </div>

      {/* Grounded Citation Evidence IDs from Hindsight Memory */}
      {evidenceIds.length > 0 && (
        <div className="pt-2 border-t border-slate-800/60">
          <div className="text-[11px] font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            Hindsight Grounded Evidence Citations ({evidenceIds.length} Memory Records):
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
            {evidenceIds.map((eid, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-950 text-indigo-300 border border-indigo-900/50"
                title={`Memory ID: ${eid}`}
              >
                {eid.slice(0, 8)}...
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
