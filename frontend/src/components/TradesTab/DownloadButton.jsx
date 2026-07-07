import React, { useState } from 'react';
import { Download, Check } from 'lucide-react';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function DownloadButton() {
  const [downloaded, setDownloaded] = useState(false);

  const handleDownload = () => {
    window.location.href = `${BASE_URL}/trades/download`;
    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 2000);
  };

  return (
    <button
      onClick={handleDownload}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 16px',
        background: downloaded ? '#10b98122' : 'rgba(245, 158, 11, 0.1)',
        border: `1px solid ${downloaded ? '#10b981' : '#f59e0b'}`,
        borderRadius: 8,
        color: downloaded ? '#10b981' : '#f59e0b',
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'all 0.2s',
        letterSpacing: 0.3,
      }}
      onMouseEnter={e => { if (!downloaded) e.currentTarget.style.background = 'rgba(245, 158, 11, 0.2)'; }}
      onMouseLeave={e => { if (!downloaded) e.currentTarget.style.background = 'rgba(245, 158, 11, 0.1)'; }}
    >
      {downloaded ? <Check size={14} /> : <Download size={14} />}
      {downloaded ? 'Downloaded' : 'Export trades.csv'}
    </button>
  );
}
