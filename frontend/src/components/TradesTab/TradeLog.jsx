import React, { useState } from 'react';

const ACTION_COLORS = { BUY: '#22c55e', SELL: '#ef4444', HOLD: '#f59e0b' };
const ASSETS = ['ALL', 'NVDA', 'MSFT', 'GOOGL', 'GLD', 'USO'];

export default function TradeLog({ trades }) {
  const [filter, setFilter] = useState('ALL');
  const [expanded, setExpanded] = useState(null);

  const filtered = (trades || []).filter(t => filter === 'ALL' || t.ticker === filter).slice().reverse();

  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 12, overflow: 'hidden' }}>
      <div style={{ display: 'flex', gap: 4, padding: '12px 16px', borderBottom: '1px solid #111827', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: '#4b5563', marginRight: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Filter:</span>
        {ASSETS.map(t => (
          <button key={t} onClick={() => setFilter(t)} style={{
            padding: '3px 8px', fontSize: 11, fontWeight: 600, borderRadius: 4,
            border: `1px solid ${filter === t ? '#f59e0b' : '#1f2937'}`,
            background: filter === t ? '#f59e0b22' : 'transparent',
            color: filter === t ? '#f59e0b' : '#4b5563', cursor: 'pointer',
          }}>
            {t}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: '#374151' }}>{filtered.length} trades</span>
      </div>

      <div style={{
        display: 'grid', gridTemplateColumns: '140px 60px 60px 80px 80px 80px 1fr', gap: 8,
        padding: '8px 16px', fontSize: 10, color: '#374151', textTransform: 'uppercase',
        letterSpacing: 1, borderBottom: '1px solid #0f172a',
      }}>
        <div>Time</div><div>Ticker</div><div>Action</div><div>Price</div><div>RF</div><div>P&L</div><div>Reason</div>
      </div>

      <div style={{ maxHeight: 500, overflowY: 'auto' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: '#374151', fontSize: 13 }}>
            No trades recorded yet. Pipeline runs every 60 seconds.
          </div>
        ) : filtered.map((t, i) => {
          const isExpanded = expanded === i;
          const actionColor = ACTION_COLORS[t.action] || '#6b7280';
          const pnl = parseFloat(t.pnl_day || 0);

          return (
            <div key={i} onClick={() => setExpanded(isExpanded ? null : i)} style={{
              borderBottom: '1px solid #0f172a', cursor: 'pointer',
              background: isExpanded ? '#050709' : 'transparent', transition: 'background 0.15s',
            }}>
              <div style={{
                display: 'grid', gridTemplateColumns: '140px 60px 60px 80px 80px 80px 1fr', gap: 8,
                padding: '10px 16px', alignItems: 'center', fontSize: 12,
              }}>
                <div style={{ color: '#4b5563', fontFamily: 'monospace', fontSize: 11 }}>
                  {t.timestamp?.slice(11, 19) || '—'}
                </div>
                <div style={{ color: '#f9fafb', fontWeight: 600 }}>{t.ticker}</div>
                <div style={{ color: actionColor, fontWeight: 700, fontSize: 11, letterSpacing: 0.5 }}>{t.action}</div>
                <div style={{ color: '#9ca3af', fontFamily: 'monospace' }}>
                  ${parseFloat(t.price_at_trade || 0).toFixed(2)}
                </div>
                <div style={{ color: t.rf_direction === 'UP' ? '#22c55e' : '#ef4444', fontSize: 11 }}>
                  {t.rf_direction || '—'}
                </div>
                <div style={{ color: pnl >= 0 ? '#22c55e' : '#ef4444', fontFamily: 'monospace' }}>
                  {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
                </div>
                <div style={{ color: '#6b7280', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.reason?.slice(0, 60)}...
                </div>
              </div>

              {isExpanded && (
                <div style={{ padding: '0 16px 12px 16px', borderTop: '1px solid #0f172a' }}>
                  <div style={{ padding: 12, background: '#050709', borderLeft: `3px solid ${actionColor}`, borderRadius: 4, marginTop: 8 }}>
                    <div style={{ fontSize: 10, color: '#4b5563', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>
                      Full Reasoning
                    </div>
                    <div style={{ fontSize: 12, color: '#d1d5db', lineHeight: 1.7 }}>{t.reason}</div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 16, fontSize: 11, color: '#6b7280' }}>
                      <span>Sentiment: {parseFloat(t.sentiment_score || 0).toFixed(3)}</span>
                      <span>LSTM: ${parseFloat(t.lstm_pred || 0).toFixed(2)}</span>
                      <span>RL: {t.rl_action}</span>
                      <span>Size: ${parseFloat(t.position_size || 0).toFixed(0)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
