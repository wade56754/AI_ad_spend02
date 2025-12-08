/**
 * Root Layout
 *
 * Next.js App Router root layout with providers
 * 统一入口 - 合并自 app/layout.tsx
 */

import React from 'react';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import { GlobalErrorBoundary } from '@/components/shared';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI广告代投系统',
  description: '智能化广告投放管理平台',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={`${inter.className} font-sans antialiased`}>
        <GlobalErrorBoundary>
          <Providers>{children}</Providers>
        </GlobalErrorBoundary>
      </body>
    </html>
  );
}
