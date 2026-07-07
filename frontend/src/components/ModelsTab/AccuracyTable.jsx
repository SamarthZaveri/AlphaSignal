import React from 'react';

const ASSETS = ['NVDA', 'MSFT', 'GOOGL', 'GLD', 'USO'];

export default function AccuracyTable({ metrics }) {
  const rfAcc = metrics?.rf_accuracy || {};
  const lstmMae = metrics?.lstm_mae || {};

  return (
    <div style={{
      background: '#0d1117', border: '1px solid #1f2937',
      borderRadius: 12, padding: 16,
    }}>
      <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
        Directional Accuracy by Model
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: '80px 1fr 1fr', gap: 8,
        fontSize: 10, color: '#374151', textTransform: 'uppercase',
        letterSpacing: 0.5, paddingBottom: 8, borderBottom: '1px solid #111827',
      }}>
        <div>Asset</div>
        <div>RF Accuracy (CV)</div>
        <div>LSTM MAE</div>
      </div>

      {ASSETS.map(ticker => {
        const acc = rfAcc[ticker];
        const mae = lstmMae[ticker];
        const accPct = acc ? acc * 100 : null;
        const isGood = accPct && accPct > 52;

        return (
          <div key={ticker} style={{
            display: 'grid', gridTemplateColumns: '80px 1fr 1fr', gap: 8,
            padding: '12px 0', borderBottom: '1px solid #0a0d12',
            alignItems: 'center',
          }}>
            <div style={{ fontWeight: 700, color: '#f9fafb', fontSize: 13 }}>{ticker}</div>

            <div>
              {accPct !== null ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 80, height: 6, background: '#1f2937', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{
                      width: `${Math.min(accPct, 100)}%`, height: '100%',
                      background: isGood ? '#22c55e' : '#f59e0b',
                      borderRadius: 3,
                    }} />
                  </div>
                  <span style={{ fontFamily: 'monospace', fontSize: 12, color: isGood ? '#22c55e' : '#f59e0b' }}>
                    {accPct.toFixed(1)}%
                  </span>
                </div>
              ) : (
                <span style={{ color: '#374151', fontSize: 12 }}>pending retrain</span>
              )}
            </div>

            <div style={{ fontFamily: 'monospace', fontSize: 12, color: mae !== undefined ? '#9ca3af' : '#374151' }}>
              {mae !== undefined ? mae.toFixed(6) : 'pending retrain'}
            </div>
          </div>
        );
      })}

      <div style={{ marginTop: 12, fontSize: 11, color: '#374151', lineHeight: 1.6 }}>
        Random baseline for binary direction is 50%. CV accuracy uses time-series
        walk-forward splits — no lookahead bias.
      </div>
    </div>
  );
}
