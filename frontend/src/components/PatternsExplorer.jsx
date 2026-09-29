import React from 'react';
import { Layers, ShieldCheck, AlertCircle } from 'lucide-react';

export default function PatternsExplorer({ patterns }) {
  const PATTERNS_LIST = [
    {
      id: 'P1',
      service: 'payments-api',
      type: 'config',
      timing: 'Friday hour >= 16',
      title: 'Friday Peak Settlement Connection Pool Exhaustion',
      mechanism: 'Reducing pool_max_connections (e.g. 50 -> 15) while increasing keepalive causes thread starvation during peak batch runs, triggering 504 cascades.',
      runbook: 'RB-PAY-04',
      fix: 'Revert pool_max to 50+, keepalive to 3000ms, rolling pod restart.'
    },
    {
      id: 'P2',
      service: 'ledger-service',
      type: 'migration',
      timing: 'Any day',
      title: 'Unbackfilled Column Drop Migration',
      mechanism: 'Dropping transaction_status or ledger column without 2-phase code transition causes downstream reporting and search-indexer crashloops.',
      runbook: 'RB-DB-02',
      fix: 'Expand-contract migration; restore column with dummy default until code backfilled.'
    },
    {
      id: 'P3',
      service: 'auth-service',
      type: 'dependency-bump',
      timing: 'Midweek',
      title: 'pyjwt Major Version Upgrade Incompatibility',
      mechanism: 'Breaking API changes in JWT verification algorithm parameter causes checkout-web auth token validation to return 401 Unauthorized.',
      runbook: 'RB-SEC-09',
      fix: 'Pin pyjwt dependency and implement dual-signature verification adapter.'
    },
    {
      id: 'P4',
      service: 'checkout-web',
      type: 'feature-flag',
      timing: 'Peak traffic',
      title: 'checkout_v2 Feature Flag & Low Cache TTL Race',
      mechanism: 'Enabling checkout_v2 while cache TTL is set < 60s causes thundering-herd cart state invalidations and payment double-charges.',
      runbook: 'RB-WEB-05',
      fix: 'Disable feature flag, reset cache TTL to 300s, flush Redis session keys.'
    },
    {
      id: 'P5',
      service: 'base-image bump',
      type: 'Dockerfile',
      timing: 'CI stage',
      title: 'Base Image glibc ABI Incompatibility (CI Build Failure)',
      mechanism: 'Upgrading base alpine/debian image introduces incompatible glibc symbol mismatch with proprietary payment cryptographic binaries.',
      runbook: 'RB-CI-01',
      fix: 'Pin glibc compatible base image tag in Dockerfile.'
    },
    {
      id: 'P6',
      service: 'infra-terraform',
      type: 'security-group',
      timing: 'Any day',
      title: 'Security Group Egress Restriction Outage',
      mechanism: 'Restricting egress security group ports blocks outbound HTTPS webhooks to banking gateway partners.',
      runbook: 'RB-INFRA-07',
      fix: 'Revert terraform egress CIDR rule; restore port 443 outbound gateway.'
    }
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            Synthesized Recurring Failure Patterns (Hindsight Reflect)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Systemic operational risk patterns consolidated across memories and verified runbooks
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {PATTERNS_LIST.map((p) => (
          <div key={p.id} className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 space-y-2 flex flex-col justify-between">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {p.id}: {p.service}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">{p.type}</span>
              </div>
              <h3 className="text-xs font-bold text-slate-100">{p.title}</h3>
              <p className="text-[11px] text-slate-400 leading-relaxed">{p.mechanism}</p>
            </div>
            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Runbook:</span>
              <span className="font-mono text-emerald-300 font-semibold">{p.runbook}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
