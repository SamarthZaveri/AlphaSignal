import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const ASSETS = ['NVDA', 'MSFT', 'GOOGL', 'GLD', 'USO'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div style={{
      background: '#0d1117', border: '1px solid #1f2937',
      borderRadius: 6, padding: '8px 12px', fontSize: 12,
    }}>
      <div style={{ color: '#d1d5db' }}>{d.payload.name}</div>
      <div style={{ color: '#f59e0b', fontFamily: 'monospace', fontWeight: 700 }}>
        {(d.value * 100).toFixed(1)}%
      </div>
    </div>
  );
}

export default function FeatureImportance({ importances }) {
  const [selected, setSelected] = useState('NVDA');
  const data = importances?.[selected];

  const chartData = data
    ? Object.entries(data).slice(0, 8).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div style={{
      background: '#0d1117', border: '1px solid #1f2937',
      borderRadius: 12, padding: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1 }}>
          RF Feature Importance
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {ASSETS.map(t => (
            <button
              key={t}
              onClick={() => setSelected(t)}
              style={{
                padding: '3px 8px', fontSize: 10, fontWeight: 600,
                borderRadius: 4,
                border: `1px solid ${selected === t ? '#f59e0b' : '#1f2937'}`,
                background: selected === t ? '#f59e0b22' : 'transparent',
                color: selected === t ? '#f59e0b' : '#4b5563',
                cursor: 'pointer',
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {chartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#111827" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#374151', fontSize: 10 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
            <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={90} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff08' }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={i === 0 ? '#f59e0b' : '#92400e'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div style={{ padding: 48, textAlign: 'center', color: '#374151', fontSize: 12 }}>
          No importance data yet — awaiting first retrain cycle.
        </div>
      )}
    </div>
  );
}
