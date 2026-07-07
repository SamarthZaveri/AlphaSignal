import React, { useState, useEffect } from 'react';
import TradeLog from './TradesTab/TradeLog';
import PnLChart from './TradesTab/PnLChart';
import DownloadButton from './TradesTab/DownloadButton';
import { apiFetch } from '../hooks/useApi';

export default function TradesTabPage({ portfolio }) {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const data = await apiFetch('/trades?limit=200');
        setTrades(data.trades || []);
      } catch (e) {
        console.error('Failed to fetch trades:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchTrades();
    const interval = setInterval(fetchTrades, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <PnLChart portfolio={portfolio} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#f9fafb' }}>Trade History</div>
        <DownloadButton />
      </div>

      <TradeLog trades={trades} />

      {loading && (
        <div style={{ textAlign: 'center', color: '#374151', fontSize: 12, padding: 16 }}>
          Loading trades...
        </div>
      )}
    </div>
  );
}
