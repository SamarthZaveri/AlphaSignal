import React from 'react';

const COLORS = {
  UP: '#22c55e', DOWN: '#ef4444', HOLD: '#f59e0b',
  BUY: '#22c55e', SELL: '#ef4444',
  POSITIVE: '#22c55e', 'STRONGLY POSITIVE': '#16a34a',
  NEGATIVE: '#ef4444', 'STRONGLY NEGATIVE': '#dc2626',
  NEUTRAL: '#6b7280', HIGH: '#22c55e', LOW: '#6b7280',
};

function Badge({ label, value, color, sub }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: `1px solid ${color}33`,
      borderRadius: 8, padding: '10px 14px', minWidth: 110, flex: 1,
    }}>
      <div style={{ fontSize: 10, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color, fontFamily: 'monospace' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export default function SignalBadges({ signal }) {
  if (!signal) {
    return (
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {['RF', 'LSTM', 'NLP', 'PPO'].map(label => (
          <div key={label} style={{
            background: 'rgba(255,255,255,0.03)', border: '1px solid #1f2937',
            borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 110, height: 72,
          }}>
            <div style={{ fontSize: 10, color: '#374151', textTransform: 'uppercase' }}>{label}</div>
            <div style={{ marginTop: 6, height: 18, background: '#111827', borderRadius: 4 }} />
          </div>
        ))}
      </div>
    );
  }

  const rfColor = COLORS[signal.rf_direction] || '#6b7280';
  const lstmColor = signal.lstm_predicted_pct > 0 ? COLORS.UP : COLORS.DOWN;
  const sentColor = COLORS[signal.sentiment_label] || '#6b7280';
  const actionColor = COLORS[signal.action] || '#f59e0b';

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <Badge label="Random Forest" value={signal.rf_direction} color={rfColor}
        sub={`${(signal.rf_prob_up * 100).toFixed(0)}% conf · ${signal.rf_confidence}`} />
      <Badge label="LSTM" value={`${signal.lstm_predicted_pct > 0 ? '+' : ''}${signal.lstm_predicted_pct?.toFixed(2)}%`}
        color={lstmColor} sub={`Target: $${signal.lstm_predicted_close?.toFixed(2)}`} />
      <Badge label="Sentiment" value={signal.sentiment_label?.replace('STRONGLY ', 'STR. ')}
        color={sentColor} sub={`Score: ${signal.sentiment_score?.toFixed(3)}`} />
      <Badge label="PPO Agent" value={signal.action} color={actionColor}
        sub={`Conf: ${(signal.rl_confidence * 100).toFixed(0)}%`} />
    </div>
  );
}
