// app/providers.tsx
'use client';

import { SWRConfig } from 'swr';
import { ThemeProvider } from 'next-themes';
import type { ReactNode } from 'react';

/**
 * 全局 Provider 配置
 * ⚠️ 必须是 Client Component
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <SWRConfig
        value={{
          refreshInterval: 0, // 禁用自动轮询（按需启用）
          revalidateOnFocus: false, // 禁用窗口聚焦时重新验证
          revalidateOnReconnect: true, // 启用重新连接时验证
          dedupingInterval: 2000, // 2秒内相同请求去重
          shouldRetryOnError: false, // 禁用自动重试
          onError: (error) => {
            console.error('SWR Error:', error);
          },
        }}
      >
        {children}
      </SWRConfig>
    </ThemeProvider>
  );
}
