'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

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
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            gap: '1rem',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>应用程序错误</h2>
          <p style={{ color: '#666' }}>{error.message || '发生了一个错误'}</p>
          <Button onClick={reset} className="bg-black text-white hover:bg-black/90">
            重试
          </Button>
        </div>
      </body>
    </html>
  );
}
