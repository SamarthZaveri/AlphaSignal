import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

function MetricBlock({ label, value, suffix = '', color = '#f9fafb', icon }) {
  return (
    <div style={{ flex: 1, minWidth: 120 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        {icon}
        <span style={{ fontSize: 10, color: '#4b5563', textTransform: 'uppercase', letterSpacing: 1 }}>{label}</span>
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color, fontFamily: 'monospace' }}>
        {value}{suffix}
      </div>
    </div>
  );
}

export default function SharpeCard({ portfolio }) {
  const sharpe = portfolio?.sharpe ?? 0;
  const alpha = portfolio?.alpha ?? 0;
  const pnl = portfolio?.pnl_cumulative ?? 0;
  const totalValue = portfolio?.total_value ?? 100000;

  const sharpeColor = sharpe > 1 ? '#22c55e' : sharpe > 0 ? '#f59e0b' : '#ef4444';
  const alphaColor = alpha >= 0 ? '#22c55e' : '#ef4444';
  const pnlColor = pnl >= 0 ? '#22c55e' : '#ef4444';

  return (
    <div style={{
      background: '#0d1117', border: '1px solid #1f2937',
      borderRadius: 12, padding: 16,
    }}>
      <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 16 }}>
        Risk-Adjusted Performance
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 16 }}>
        <MetricBlock
          label="Sharpe Ratio"
          value={sharpe.toFixed(2)}
          color={sharpeColor}
          icon={<Activity size={12} color="#4b5563" />}
        />
        <MetricBlock
          label="Total Value"
          value={`$${totalValue.toLocaleString()}`}
          color="#f9fafb"
        />
        <MetricBlock
          label="Cumulative P&L"
          value={`${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString()}`}
          color={pnlColor}
          icon={pnl >= 0 ? <TrendingUp size={12} color="#22c55e" /> : <TrendingDown size={12} color="#ef4444" />}
        />
      </div>

      <div style={{ display: 'flex', gap: 20, paddingTop: 16, borderTop: '1px solid #111827' }}>
        <MetricBlock
          label="Alpha vs SPY"
          value={`${alpha >= 0 ? '+' : ''}${alpha.toFixed(2)}`}
          suffix="%"
          color={alphaColor}
        />
        <MetricBlock
          label="Open Positions"
          value={portfolio?.open_positions ?? 0}
          color="#f9fafb"
        />
        <MetricBlock
          label="Win Rate"
          value={portfolio?.win_rate ?? '—'}
          suffix={portfolio?.win_rate ? '%' : ''}
          color="#9ca3af"
        />
      </div>

      <div style={{ marginTop: 16, fontSize: 11, color: '#374151', lineHeight: 1.6 }}>
        Sharpe annualized from daily paper-trading returns. A Sharpe above 1.0 is
        considered good; above 2.0 is excellent for a research strategy.
      </div>
    </div>
  );
}
