'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Dashboard error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 p-8">
      <div className="flex flex-col items-center gap-4">
        <div className="rounded-full bg-destructive/10 p-4">
          <AlertTriangle className="h-8 w-8 text-destructive" />
        </div>
        <h2 className="text-2xl font-semibold">页面加载失败</h2>
        <p className="text-muted-foreground text-center max-w-md">
          {error.message || '抱歉，加载此页面时发生错误。请尝试刷新页面。'}
        </p>
      </div>
      <div className="flex gap-4">
        <Button onClick={reset} variant="default">
          <RefreshCw className="mr-2 h-4 w-4" />
          重试
        </Button>
        <Button onClick={() => window.location.href = '/'} variant="outline">
          返回首页
        </Button>
      </div>
      {process.env.NODE_ENV === 'development' && (
        <details className="mt-4 w-full max-w-2xl">
          <summary className="cursor-pointer text-sm text-muted-foreground">
            错误详情 (开发模式)
          </summary>
          <pre className="mt-2 overflow-auto rounded-lg bg-muted p-4 text-xs">
            {error.stack}
          </pre>
        </details>
      )}
    </div>
  );
}
