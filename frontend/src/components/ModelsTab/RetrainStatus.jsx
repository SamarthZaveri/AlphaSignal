import React, { useState } from 'react';
import { RefreshCw, Clock, CheckCircle2 } from 'lucide-react';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function timeAgo(isoString) {
  if (!isoString) return 'never';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function RetrainStatus({ retrain, modelsStatus }) {
  const [triggering, setTriggering] = useState(false);

  const handleRetrain = async () => {
    setTriggering(true);
    try {
      await fetch(`${BASE_URL}/models/retrain`, { method: 'POST' });
    } catch (e) {
      console.error('Retrain trigger failed:', e);
    }
    setTimeout(() => setTriggering(false), 2000);
  };

  const inProgress = retrain?.in_progress || triggering;

  return (
    <div style={{
      background: '#0d1117', border: '1px solid #1f2937',
      borderRadius: 12, padding: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1 }}>
          Model Lifecycle
        </div>
        <button
          onClick={handleRetrain}
          disabled={inProgress}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '5px 12px', fontSize: 11, fontWeight: 600,
            background: inProgress ? '#1f293766' : 'rgba(245,158,11,0.1)',
            border: `1px solid ${inProgress ? '#374151' : '#f59e0b'}`,
            borderRadius: 6,
            color: inProgress ? '#4b5563' : '#f59e0b',
            cursor: inProgress ? 'default' : 'pointer',
          }}
        >
          <RefreshCw size={12} style={{ animation: inProgress ? 'spin 1.2s linear infinite' : 'none' }} />
          {inProgress ? 'Retraining...' : 'Trigger Retrain'}
        </button>
        <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
      </div>

      <div style={{ display: 'flex', gap: 24, marginBottom: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#4b5563', fontSize: 11, marginBottom: 4 }}>
            <Clock size={12} /> Last Retrain
          </div>
          <div style={{ fontSize: 14, color: '#d1d5db', fontFamily: 'monospace' }}>
            {timeAgo(retrain?.last_retrain)}
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#4b5563', fontSize: 11, marginBottom: 4 }}>
            <Clock size={12} /> Schedule
          </div>
          <div style={{ fontSize: 14, color: '#d1d5db', fontFamily: 'monospace' }}>
            Sundays 02:00 UTC
          </div>
        </div>
      </div>

      <div style={{ paddingTop: 12, borderTop: '1px solid #111827' }}>
        <div style={{ fontSize: 11, color: '#4b5563', marginBottom: 8 }}>Checkpoint Status</div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {['rf', 'lstm'].map(modelType => {
            const tickers = modelsStatus?.[modelType] || {};
            const loaded = Object.values(tickers).filter(Boolean).length;
            const total = Object.keys(tickers).length || 5;
            const allLoaded = loaded === total && total > 0;
            return (
              <div key={modelType} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <CheckCircle2 size={14} color={allLoaded ? '#22c55e' : '#374151'} />
                <span style={{ fontSize: 12, color: '#9ca3af', textTransform: 'uppercase' }}>
                  {modelType}: {loaded}/{total || 5}
                </span>
              </div>
            );
          })}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <CheckCircle2 size={14} color={modelsStatus?.ppo ? '#22c55e' : '#374151'} />
            <span style={{ fontSize: 12, color: '#9ca3af' }}>PPO: {modelsStatus?.ppo ? 'loaded' : 'heuristic fallback'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
