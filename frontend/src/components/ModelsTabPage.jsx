import React, { useState, useEffect } from 'react';
import AccuracyTable from './ModelsTab/AccuracyTable';
import SharpeCard from './ModelsTab/SharpeCard';
import RetrainStatus from './ModelsTab/RetrainStatus';
import FeatureImportance from './ModelsTab/FeatureImportance';
import { apiFetch } from '../hooks/useApi';

export default function ModelsTabPage({ portfolio }) {
  const [metrics, setMetrics] = useState(null);
  const [modelsStatus, setModelsStatus] = useState(null);
  const [importances, setImportances] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [m, s, fi] = await Promise.all([
          apiFetch('/metrics'),
          apiFetch('/models/status'),
          apiFetch('/models/feature-importance'),
        ]);
        setMetrics(m);
        setModelsStatus(s);
        setImportances(fi);
      } catch (e) {
        console.error('Failed to fetch model data:', e);
      }
    };
    fetchAll();
    const interval = setInterval(fetchAll, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SharpeCard portfolio={portfolio} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <AccuracyTable metrics={metrics} />
        <FeatureImportance importances={importances} />
      </div>

      <RetrainStatus retrain={modelsStatus?.retrain} modelsStatus={modelsStatus} />

      {/* Architecture explainer */}
      <div style={{
        background: '#0d1117', border: '1px solid #1f2937',
        borderRadius: 12, padding: 16,
      }}>
        <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
          Sequential Inference Pipeline
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', fontSize: 12 }}>
          {[
            { label: 'Price/Volume', color: '#6b7280' },
            { label: 'Random Forest', color: '#3b82f6' },
            { label: 'LSTM', color: '#10b981' },
            { label: 'VADER NLP', color: '#f59e0b' },
            { label: 'PPO Agent', color: '#ef4444' },
            { label: 'Trade + Reason', color: '#a855f7' },
          ].map((step, i, arr) => (
            <React.Fragment key={step.label}>
              <div style={{
                padding: '6px 12px', borderRadius: 6,
                background: `${step.color}1a`, border: `1px solid ${step.color}44`,
                color: step.color, fontWeight: 600,
              }}>
                {step.label}
              </div>
              {i < arr.length - 1 && <span style={{ color: '#374151' }}>→</span>}
            </React.Fragment>
          ))}
        </div>
        <div style={{ marginTop: 12, fontSize: 11, color: '#374151', lineHeight: 1.6 }}>
          Each model's output becomes an input feature for the next. RF direction probability
          and LSTM predicted return feed PPO's observation vector alongside live sentiment —
          the only model that acts is PPO; the rest are signal generators.
        </div>
      </div>
    </div>
  );
}
