import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL ||
  (window.location.protocol === 'https:'
    ? `wss://${window.location.host}/ws`
    : `ws://localhost:8000/ws`);

export function useWebSocket() {
  const [connected, setConnected] = useState(false);
  const [signals, setSignals] = useState({});
  const [portfolio, setPortfolio] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const reconnectCount = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectCount.current = 0;
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000);
        ws._pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'pong' || data.type === 'heartbeat') return;
          if (data.signals) setSignals(data.signals);
          if (data.portfolio) setPortfolio(data.portfolio);
          if (data.timestamp) setLastUpdate(data.timestamp);
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (ws._pingInterval) clearInterval(ws._pingInterval);
        const delay = Math.min(1000 * Math.pow(2, reconnectCount.current), 30000);
        reconnectCount.current++;
        reconnectTimer.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        setError('Connection error — retrying...');
        ws.close();
      };
    } catch (e) {
      setError(`Failed to connect: ${e.message}`);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { connected, signals, portfolio, lastUpdate, error };
}
