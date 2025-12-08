/**
 * App Providers
 *
 * Central provider wrapper for:
 * - React Query (数据获取)
 * - ThemeProvider (主题切换)
 * - NuqsAdapter (URL 状态管理)
 * - Toaster (通知提示)
 */

'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider } from 'next-themes';
import { NuqsAdapter } from 'nuqs/adapters/next/app';
import { Toaster, toast } from 'sonner';

// Create a client with sensible defaults and global error handling
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
      onError: (error: Error) => {
        console.error('Mutation error:', error);
        // Global error toast for mutations
        toast.error(error.message || '操作失败，请重试');
      },
    },
  },
});

// Global query error handler
queryClient.getQueryCache().config.onError = (error: Error) => {
  console.error('Query error:', error);
  // Only show toast for non-404 errors
  if (!error.message?.includes('404')) {
    toast.error(error.message || '数据加载失败');
  }
};

export interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <NuqsAdapter>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster
            richColors
            position="top-right"
            toastOptions={{
              duration: 4000,
            }}
          />
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </QueryClientProvider>
      </ThemeProvider>
    </NuqsAdapter>
  );
}

export default Providers;
