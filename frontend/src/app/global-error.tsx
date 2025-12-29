'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Global error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: '1rem',
          fontFamily: 'system-ui, sans-serif',
        }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>应用程序错误</h2>
          <p style={{ color: '#666' }}>{error.message || '发生了一个错误'}</p>
          <button
            onClick={reset}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#000',
              color: '#fff',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
            }}
          >
            重试
          </button>
        </div>
      </body>
    </html>
  );
}
