import React, { useState } from 'react';

const ASSETS = ['NVDA', 'MSFT', 'GOOGL', 'GLD', 'USO'];

function SentimentBar({ score }) {
  const pct = ((score + 1) / 2) * 100;
  const color = score > 0.05 ? '#22c55e' : score < -0.05 ? '#ef4444' : '#f59e0b';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 60, height: 4, background: '#1f2937', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.5s' }} />
      </div>
      <span style={{ fontSize: 11, color, fontFamily: 'monospace' }}>
        {score > 0 ? '+' : ''}{score?.toFixed(3)}
      </span>
    </div>
  );
}

export default function NewsTicker({ signals, sentiment }) {
  const [selected, setSelected] = useState('NVDA');
  const sig = signals?.[selected];
  const sent = sentiment?.[selected] || sig;

  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 12, padding: 16, height: '100%' }}>
      <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
        Sentiment Feed
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: 12, flexWrap: 'wrap' }}>
        {ASSETS.map(t => {
          const s = signals?.[t]?.sentiment_score || 0;
          const color = s > 0.05 ? '#22c55e' : s < -0.05 ? '#ef4444' : '#f59e0b';
          return (
            <button key={t} onClick={() => setSelected(t)} style={{
              padding: '4px 8px', fontSize: 11, fontWeight: 600, borderRadius: 4,
              border: `1px solid ${selected === t ? color : '#1f2937'}`,
              background: selected === t ? `${color}22` : 'transparent',
              color: selected === t ? color : '#4b5563', cursor: 'pointer', transition: 'all 0.2s',
            }}>
              {t}
            </button>
          );
        })}
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: '#4b5563', marginBottom: 6 }}>Compound Score</div>
        <SentimentBar score={sig?.sentiment_score || 0} />
        <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
          {sig?.sentiment_label || 'NEUTRAL'} · {sent?.headline_count || 0} headlines
        </div>
      </div>

      <div>
        <div style={{ fontSize: 11, color: '#4b5563', marginBottom: 8 }}>Recent Headlines</div>
        {(sig?.top_headlines || []).map((h, i) => (
          <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid #111827', fontSize: 12, color: '#9ca3af', lineHeight: 1.4 }}>
            <span style={{
              display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
              background: sig.sentiment_score > 0.05 ? '#22c55e' : sig.sentiment_score < -0.05 ? '#ef4444' : '#f59e0b',
              marginRight: 8, verticalAlign: 'middle',
            }} />
            {h}
          </div>
        ))}
        {(!sig?.top_headlines || sig.top_headlines.length === 0) && (
          <div style={{ color: '#374151', fontSize: 12, fontStyle: 'italic' }}>Awaiting pipeline...</div>
        )}
      </div>

      {sig?.reason && (
        <div style={{ marginTop: 16, padding: 10, background: '#050709', border: '1px solid #1f2937', borderLeft: '3px solid #f59e0b', borderRadius: 4 }}>
          <div style={{ fontSize: 10, color: '#92400e', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
            Agent Reasoning
          </div>
          <div style={{ fontSize: 11, color: '#d1d5db', lineHeight: 1.6 }}>{sig.reason}</div>
        </div>
      )}
    </div>
  );
}
