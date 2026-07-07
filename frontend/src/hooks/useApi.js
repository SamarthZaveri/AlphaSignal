import { useState, useEffect, useCallback } from 'react';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export function useApi(path, interval = null) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch_ = useCallback(async () => {
    try {
      const result = await apiFetch(path);
      setData(result);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    fetch_();
    if (interval) {
      const timer = setInterval(fetch_, interval);
      return () => clearInterval(timer);
    }
  }, [fetch_, interval]);

  return { data, loading, error, refetch: fetch_ };
}
