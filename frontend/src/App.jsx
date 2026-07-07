import React, { useState } from 'react';
import { Activity, TrendingUp, Cpu, Github } from 'lucide-react';
import { useWebSocket } from './hooks/useWebSocket';
import LiveTabPage from './components/LiveTabPage';
import TradesTabPage from './components/TradesTabPage';
import ModelsTabPage from './components/ModelsTabPage';

const TABS = [
  { id: 'live', label: 'Live', icon: Activity },
  { id: 'trades', label: 'Trades', icon: TrendingUp },
  { id: 'models', label: 'Models', icon: Cpu },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const { connected, signals, portfolio, lastUpdate, error } = useWebSocket();

  return (
    <div style={{
      minHeight: '100vh',
      background: '#06080c',
      backgroundImage: `
        radial-gradient(circle at 15% 8%, rgba(245, 158, 11, 0.06) 0%, transparent 35%),
        radial-gradient(circle at 85% 92%, rgba(16, 185, 129, 0.05) 0%, transparent 35%)
      `,
      fontFamily: "'JetBrains Mono', 'SF Mono', 'Consolas', monospace",
      color: '#e5e7eb',
    }}>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');
        * { box-sizing: border-box; }
        body { margin: 0; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0a0d12; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #374151; }
      `}</style>

      {/* Header */}
      <header style={{
        borderBottom: '1px solid #161b22',
        padding: '18px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        background: 'rgba(6,8,12,0.92)',
        backdropFilter: 'blur(8px)',
        zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 800, fontSize: 16, color: '#06080c',
          }}>
            α
          </div>
          <div>
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700, fontSize: 17, color: '#f9fafb', letterSpacing: -0.3,
            }}>
              AlphaSignal
            </div>
            <div style={{ fontSize: 10, color: '#4b5563', letterSpacing: 0.5 }}>
              RF → LSTM → NLP → PPO · paper trading
            </div>
          </div>
        </div>

        {/* Tab nav */}
        <nav style={{ display: 'flex', gap: 4, background: '#0d1117', padding: 4, borderRadius: 10, border: '1px solid #1f2937' }}>
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '7px 16px', fontSize: 13, fontWeight: 600,
                  borderRadius: 7, border: 'none', cursor: 'pointer',
                  background: active ? '#f59e0b' : 'transparent',
                  color: active ? '#06080c' : '#6b7280',
                  transition: 'all 0.15s',
                }}
              >
                <Icon size={14} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          style={{ color: '#4b5563', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, textDecoration: 'none' }}
        >
          <Github size={16} />
        </a>
      </header>

      {/* Error banner */}
      {error && (
        <div style={{
          background: '#7f1d1d22', borderBottom: '1px solid #7f1d1d',
          padding: '8px 32px', fontSize: 12, color: '#fca5a5', textAlign: 'center',
        }}>
          {error}
        </div>
      )}

      {/* Main content */}
      <main style={{ padding: '24px 32px', maxWidth: 1400, margin: '0 auto' }}>
        {activeTab === 'live' && (
          <LiveTabPage signals={signals} portfolio={portfolio} connected={connected} lastUpdate={lastUpdate} />
        )}
        {activeTab === 'trades' && (
          <TradesTabPage portfolio={portfolio} />
        )}
        {activeTab === 'models' && (
          <ModelsTabPage portfolio={portfolio} />
        )}
      </main>

      <footer style={{
        textAlign: 'center', padding: '24px 32px', color: '#1f2937', fontSize: 11,
        borderTop: '1px solid #111827', marginTop: 24,
      }}>
        Paper trading only · Not financial advice · Data via yfinance, refreshed every 60s
      </footer>
    </div>
  );
}
