'use client';

import React from 'react';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  header: React.ReactNode;
  className?: string;
}

export default function AppLayout({
  children,
  sidebar,
  header,
  className = ''
}: AppLayoutProps) {
  const { theme } = useTheme();

  return (
    <div
      className={cn(
        'min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200',
        className
      )}
      data-theme={theme}
    >
      <div className="flex h-screen overflow-hidden">
        {/* 侧边栏 */}
        {sidebar}

        {/* 主内容区域 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 顶部栏 */}
          {header}

          {/* 主要内容 */}
          <main className="flex-1 overflow-auto">
            <div className="h-full">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}