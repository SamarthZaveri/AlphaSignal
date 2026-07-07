import React from 'react';
import PriceChart from './LiveTab/PriceChart';
import SignalBadges from './LiveTab/SignalBadges';
import NewsTicker from './LiveTab/NewsTicker';

const ASSETS = ['NVDA', 'MSFT', 'GOOGL', 'GLD', 'USO'];

export default function LiveTab({ signals, portfolio, connected, lastUpdate }) {
  const prices = {};
  ASSETS.forEach(t => { prices[t] = signals?.[t]?.price; });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Status bar */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '10px 16px', background: '#0d1117', border: '1px solid #1f2937',
        borderRadius: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: connected ? '#22c55e' : '#ef4444',
            boxShadow: connected ? '0 0 8px #22c55e' : 'none',
            animation: connected ? 'pulse 2s infinite' : 'none',
          }} />
          <span style={{ fontSize: 12, color: '#9ca3af' }}>
            {connected ? 'Live feed connected' : 'Reconnecting...'}
          </span>
          <style>{`@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.4 } }`}</style>
        </div>
        <div style={{ fontSize: 11, color: '#4b5563', fontFamily: 'monospace' }}>
          Last update: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : '—'}
        </div>
      </div>

      {/* Asset grid: price chart + signal badges per ticker */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {ASSETS.map(ticker => (
            <div key={ticker} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <PriceChart
                ticker={ticker}
                currentPrice={prices[ticker]}
                currentSignal={signals?.[ticker]}
              />
              <SignalBadges signal={signals?.[ticker]} />
            </div>
          ))}
        </div>

        {/* Sentiment / reasoning sidebar */}
        <div style={{ position: 'sticky', top: 16, height: 'fit-content' }}>
          <NewsTicker signals={signals} />
        </div>
      </div>
    </div>
  );
}
