import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { TrendingDown, Activity } from 'lucide-react';

export default function LearningCurveChart({ data }) {
  // Sample every 2 steps or show all 150 points
  const chartData = (data || []).map((d) => ({
    step: d.step,
    deploy_id: d.deploy_id,
    category: d.category,
    'Memory-On F1': Number(d.mem_on_f1?.toFixed(4) || 0),
    'Memory-Off F1': Number(d.mem_off_f1?.toFixed(4) || 0)
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const row = chartData[label - 1] || {};
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
          <p className="font-bold text-white">
            Step {label}: <span className="font-mono text-emerald-400">{row.deploy_id}</span>
          </p>
          <p className="text-slate-400 text-[11px]">Cohort: {row.category}</p>
          <div className="pt-1 space-y-0.5 font-mono">
            <p className="text-emerald-400">
              Memory-On F1: {payload[0]?.value}
            </p>
            <p className="text-blue-400">
              Memory-Off F1: {payload[1]?.value}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Empirical Learning Trajectory: Rolling Incident F1 Score
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological F1-score progression evaluated at Risk &ge; 0.5 across all 150 deployments
          </p>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-400">
          <TrendingDown className="w-3.5 h-3.5 text-amber-400" />
          <span>Reflects early incident surge & subsequent leveling off</span>
        </div>
      </div>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="step"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              tickMargin={6}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              domain={[0, 1.05]}
              tickLine={false}
              tickMargin={6}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="Memory-On F1"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, fill: '#10b981' }}
            />
            <Line
              type="monotone"
              dataKey="Memory-Off F1"
              stroke="#60a5fa"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              activeDot={{ r: 5, fill: '#60a5fa' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[11px] text-slate-500 border-t border-slate-800/60 pt-2 flex justify-between">
        <span>Step 1: 0.00 (Pre-incident baseline)</span>
        <span>Step 15: 1.00 (Post dep-111 detection)</span>
        <span>Step 45: 0.46 (Decoy & variety phase)</span>
        <span>Step 150: 0.4444 (Final stabilized)</span>
      </div>
    </div>
  );
}
