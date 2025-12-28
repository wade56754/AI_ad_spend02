'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { Toaster } from 'sonner';

/**
 * TanStack Query 配置优化 (Phase 3 TASK-PERF-004)
 *
 * staleTime: 数据在多长时间内被认为是新鲜的 (不会重新获取)
 * gcTime: 缓存数据在内存中保留多长时间 (formerly cacheTime)
 * refetchOnWindowFocus: 窗口聚焦时是否重新获取
 * retry: 失败重试策略
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = React.useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // 数据在 2 分钟内认为是新鲜的
        staleTime: 1000 * 60 * 2,
        // 缓存数据保留 10 分钟 (即使组件卸载)
        gcTime: 1000 * 60 * 10,
        // 窗口聚焦时不自动重新获取 (减少不必要的请求)
        refetchOnWindowFocus: false,
        // 标签页切换时不重新获取
        refetchOnReconnect: 'always',
        // 指数退避重试: 1s, 2s, 4s (最多 3 次)
        retry: 3,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      },
      mutations: {
        // mutation 失败重试 1 次
        retry: 1,
      },
    },
  }));

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        {children}
        <Toaster position="top-right" richColors />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
