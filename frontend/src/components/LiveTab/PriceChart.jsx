import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';

const ASSET_COLORS = { NVDA: '#10b981', MSFT: '#3b82f6', GOOGL: '#f59e0b', GLD: '#eab308', USO: '#f97316' };

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ color: d.color, fontWeight: 700, fontFamily: 'monospace' }}>
        ${Number(d.value).toFixed(2)}
      </div>
    </div>
  );
}

export default function PriceChart({ ticker, currentPrice, currentSignal }) {
  const [history, setHistory] = useState([]);
  const color = ASSET_COLORS[ticker] || '#6b7280';

  useEffect(() => {
    if (!currentPrice || !ticker) return;
    const point = {
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      price: currentPrice,
    };
    setHistory(prev => [...prev, point].slice(-60));
  }, [currentPrice, ticker]);

  const minPrice = history.length ? Math.min(...history.map(d => d.price)) * 0.999 : 0;
  const maxPrice = history.length ? Math.max(...history.map(d => d.price)) * 1.001 : 100;
  const firstPrice = history[0]?.price;
  const priceDelta = firstPrice && currentPrice ? ((currentPrice - firstPrice) / firstPrice * 100) : 0;
  const isUp = priceDelta >= 0;

  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 12, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#f9fafb', letterSpacing: 1 }}>{ticker}</span>
            <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 4, background: `${color}22`, color }}>
              {currentSignal?.action || 'LOADING'}
            </span>
          </div>
          <div style={{ fontSize: 22, fontWeight: 700, color: '#f9fafb', fontFamily: 'monospace', marginTop: 2 }}>
            ${currentPrice?.toFixed(2) || '—'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: isUp ? '#22c55e' : '#ef4444', fontFamily: 'monospace' }}>
            {isUp ? '+' : ''}{priceDelta.toFixed(3)}%
          </div>
          <div style={{ fontSize: 11, color: '#4b5563', marginTop: 2 }}>session</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={history} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`grad-${ticker}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#111827" />
          <XAxis dataKey="time" hide />
          <YAxis domain={[minPrice, maxPrice]} hide />
          <Tooltip content={<CustomTooltip />} />
          {firstPrice && <ReferenceLine y={firstPrice} stroke="#374151" strokeDasharray="4 4" />}
          <Area type="monotone" dataKey="price" stroke={color} strokeWidth={2}
            fill={`url(#grad-${ticker})`} dot={false} animationDuration={200} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
