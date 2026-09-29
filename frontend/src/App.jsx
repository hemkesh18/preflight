import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HeadlineMetrics from './components/HeadlineMetrics';
import LearningCurveChart from './components/LearningCurveChart';
import ConfusionMatrixCard from './components/ConfusionMatrixCard';
import GateSimulator from './components/GateSimulator';
import PatternsExplorer from './components/PatternsExplorer';
import DeploymentTable from './components/DeploymentTable';
import PostIncidentForm from './components/PostIncidentForm';

// Bundled fallback data in case FastAPI is not started
import defaultReplayData from './data/replay.json';

export default function App() {
  const [replayData, setReplayData] = useState(defaultReplayData);
  const [selectedDeployId, setSelectedDeployId] = useState('dep-131');
  const [demoMode, setDemoMode] = useState('cached');
  const [fallbackBanner, setFallbackBanner] = useState(
    'Offline Demonstration Mode: Serving verified replay telemetry with zero external network dependencies.'
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Attempt to load live data from FastAPI backend
    async function fetchApi() {
      try {
        const healthRes = await fetch('/api/health');
        if (healthRes.ok) {
          const health = await healthRes.json();
          const mode = health.demo_mode || 'cached';
          setDemoMode(mode);
          if (mode === 'cached') {
            setFallbackBanner(
              'Offline Demonstration Mode: Serving verified replay telemetry with zero external network dependencies.'
            );
          } else {
            setFallbackBanner(null);
          }
        }
        const replayRes = await fetch('/api/replay');
        if (replayRes.ok) {
          const data = await replayRes.json();
          setReplayData(data);
        }
      } catch (err) {
        setFallbackBanner('FastAPI backend offline; serving bundled backtest results.');
      }
    }
    fetchApi();
  }, []);

  const metadata = replayData?.metadata || {};
  const headlineMetrics = replayData?.headline_metrics || {};
  const rollingMetrics = replayData?.rolling_metrics || [];
  const records = replayData?.records || [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      <Header
        metadata={metadata}
        demoMode={demoMode}
        fallbackBanner={fallbackBanner}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top: Headline Metrics & Cavet Banner */}
        <HeadlineMetrics metrics={headlineMetrics} />

        {/* Center: Interactive CI/CD Release Gate Simulator (Before/After) */}
        <GateSimulator
          records={records}
          selectedDeployId={selectedDeployId}
          onSelectDeploy={(id) => setSelectedDeployId(id)}
        />

        {/* Post-Incident Feedback & Runbook Ingestion Form */}
        <PostIncidentForm />

        {/* Mid: Empirical Learning Curve & Confusion Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LearningCurveChart data={rollingMetrics} />
          <ConfusionMatrixCard metrics={headlineMetrics} />
        </div>

        {/* Synthesized Systemic Patterns */}
        <PatternsExplorer />

        {/* Full 150 Deployment Stream Table */}
        <DeploymentTable
          records={records}
          selectedDeployId={selectedDeployId}
          onSelectDeploy={(id) => setSelectedDeployId(id)}
        />
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        Preflight &bull; Autonomous Release Safety Gate powered by Vectorize Hindsight Persistent Memory
      </footer>
    </div>
  );
}
