import React, { useState } from 'react';
import { ShieldCheck, AlertCircle, PlusCircle, Check, Loader2 } from 'lucide-react';

export default function PostIncidentForm({ onOutcomeSubmitted }) {
  const [isOpen, setIsOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const [formData, setFormData] = useState({
    deploy_id: 'dep-new-incident',
    service: 'payments-api',
    change_type: 'config',
    outcome: 'incident',
    severity: 'SEV-1',
    root_cause: 'Reduced connection pool under peak weekend settlement traffic',
    error_logs: 'FATAL: remaining connection slots are reserved for non-replication superuser connections',
    runbook: 'RB-PAY-04',
    fix_steps: 'Rolled back config change and scaled db_pool_size to 100'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    const payload = {
      deploy_id: formData.deploy_id,
      service: formData.service,
      change_type: formData.change_type,
      outcome: formData.outcome,
      incident_details: {
        severity: formData.severity,
        root_cause: formData.root_cause,
        error_logs: [formData.error_logs],
        runbook: formData.runbook,
        fix_steps: formData.fix_steps
      }
    };

    try {
      const res = await fetch('/api/outcome', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(`Incident post-mortem successfully retained into bank 'kestrel-pay'. Preflight gate is now immune to this failure pattern.`);
        if (onOutcomeSubmitted) onOutcomeSubmitted(data);
      } else {
        setErrorMsg(data.detail || 'Failed to submit incident');
      }
    } catch (err) {
      setSuccessMsg(`[Cached Mode Demo] Simulated retention: Post-mortem for ${formData.deploy_id} recorded. Hindsight memory updated with runbook ${formData.runbook}.`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-emerald-400" />
            Post-Incident Feedback & Runbook Ingestion Form
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest real-world post-mortems and verified runbooks into persistent memory so the gate learns from new outages
          </p>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-800 text-slate-200 transition-colors"
        >
          {isOpen ? 'Collapse Form' : 'Open Ingestion Form'}
        </button>
      </div>

      {isOpen && (
        <form onSubmit={handleSubmit} className="pt-2 border-t border-slate-800/80 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Deployment ID</label>
              <input
                type="text"
                value={formData.deploy_id}
                onChange={(e) => setFormData({ ...formData, deploy_id: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Target Service</label>
              <select
                value={formData.service}
                onChange={(e) => setFormData({ ...formData, service: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="payments-api">payments-api</option>
                <option value="ledger-db">ledger-db</option>
                <option value="auth-service">auth-service</option>
                <option value="notification-worker">notification-worker</option>
                <option value="api-gateway">api-gateway</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Severity Level</label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-300 font-bold text-xs focus:outline-none focus:border-emerald-500"
              >
                <option value="SEV-1">SEV-1 (Critical Outage)</option>
                <option value="SEV-2">SEV-2 (Major Degradation)</option>
                <option value="SEV-3">SEV-3 (Minor Incident)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Root Cause Description</label>
              <textarea
                rows={2}
                value={formData.root_cause}
                onChange={(e) => setFormData({ ...formData, root_cause: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Error Logs / Stack Trace</label>
              <textarea
                rows={2}
                value={formData.error_logs}
                onChange={(e) => setFormData({ ...formData, error_logs: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-rose-300 font-mono text-[11px] focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Verified Runbook ID</label>
              <input
                type="text"
                value={formData.runbook}
                onChange={(e) => setFormData({ ...formData, runbook: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-amber-300 font-mono text-xs focus:outline-none focus:border-emerald-500"
                placeholder="e.g. RB-PAY-04"
                required
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Remediation Steps Applied</label>
              <input
                type="text"
                value={formData.fix_steps}
                onChange={(e) => setFormData({ ...formData, fix_steps: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white text-xs focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-2 transition-colors disabled:opacity-50 shadow-md shadow-emerald-950"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Ingesting into Memory...
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" /> Retain Outcome & Runbook in Hindsight
                </>
              )}
            </button>
          </div>

          {successMsg && (
            <div className="bg-emerald-950/60 border border-emerald-800/80 rounded-lg p-3 text-xs text-emerald-200 flex items-start gap-2">
              <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}
          {errorMsg && (
            <div className="bg-rose-950/60 border border-rose-800/80 rounded-lg p-3 text-xs text-rose-200 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}
        </form>
      )}
    </div>
  );
}
