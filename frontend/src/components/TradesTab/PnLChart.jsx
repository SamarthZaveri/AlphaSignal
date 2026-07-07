import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: '#6b7280', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontFamily: 'monospace' }}>
          {p.name}: {p.value >= 0 ? '+' : ''}{p.value?.toFixed(2)}%
        </div>
      ))}
    </div>
  );
}

export default function PnLChart({ portfolio }) {
  const data = React.useMemo(() => {
    if (!portfolio) return mockData();
    return mockData(portfolio.portfolio_return_pct, portfolio.spy_return_pct);
  }, [portfolio]);

  return (
    <div style={{ background: '#0d1117', border: '1px solid #1f2937', borderRadius: 12, padding: 16 }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1 }}>
          Cumulative P&L vs SPY
        </div>
        {portfolio && (
          <div style={{ display: 'flex', gap: 24, marginTop: 6 }}>
            <div>
              <span style={{ color: '#10b981', fontFamily: 'monospace', fontSize: 18, fontWeight: 700 }}>
                {portfolio.portfolio_return_pct >= 0 ? '+' : ''}{portfolio.portfolio_return_pct?.toFixed(2)}%
              </span>
              <span style={{ color: '#4b5563', fontSize: 11, marginLeft: 6 }}>AlphaSignal</span>
            </div>
            <div>
              <span style={{ color: '#3b82f6', fontFamily: 'monospace', fontSize: 18, fontWeight: 700 }}>
                {portfolio.spy_return_pct >= 0 ? '+' : ''}{portfolio.spy_return_pct?.toFixed(2)}%
              </span>
              <span style={{ color: '#4b5563', fontSize: 11, marginLeft: 6 }}>SPY</span>
            </div>
            <div>
              <span style={{ color: portfolio.alpha >= 0 ? '#22c55e' : '#ef4444', fontFamily: 'monospace', fontSize: 18, fontWeight: 700 }}>
                {portfolio.alpha >= 0 ? '+' : ''}{portfolio.alpha?.toFixed(2)}%
              </span>
              <span style={{ color: '#4b5563', fontSize: 11, marginLeft: 6 }}>Alpha</span>
            </div>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#111827" />
          <XAxis dataKey="t" tick={{ fill: '#374151', fontSize: 10 }} />
          <YAxis tick={{ fill: '#374151', fontSize: 10 }} tickFormatter={v => `${v}%`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 11, color: '#6b7280' }} />
          <ReferenceLine y={0} stroke="#1f2937" />
          <Line type="monotone" dataKey="alpha" name="AlphaSignal" stroke="#10b981" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="spy" name="SPY" stroke="#3b82f6" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function mockData(currentAlpha = 0, currentSpy = 0) {
  const points = [];
  const days = 30;
  let alpha = 0, spy = 0;
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;

    const t = (days - i) / days;
    alpha = currentAlpha * t + (Math.random() - 0.45) * 0.3;
    spy = currentSpy * t + (Math.random() - 0.48) * 0.2;

    points.push({
      t: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      alpha: parseFloat(alpha.toFixed(2)),
      spy: parseFloat(spy.toFixed(2)),
    });
  }
  return points;
}
