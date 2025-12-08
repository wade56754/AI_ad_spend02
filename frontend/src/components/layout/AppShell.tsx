/**
 * @deprecated AppShell is deprecated. Use AppLayout instead.
 *
 * AppShell将在未来版本中移除，请使用AppLayout替代。
 * AppLayout提供更灵活的组合模式和主题支持。
 *
 * Migration guide: 请参考 docs/COMPONENT_MIGRATION.md
 *
 * @see AppLayout - 推荐的新组件
 * @since Deprecated in v2.3, will be removed in v3.0
 */

'use client';

import React from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { useState } from 'react';

interface AppShellProps {
  children: React.ReactNode;
}

/**
 * @deprecated Use AppLayout instead
 */
export default function AppShell({ children }: AppShellProps) {
  console.warn(
    '⚠️ AppShell is deprecated and will be removed in v3.0. Please migrate to AppLayout. ' +
    'See docs/COMPONENT_MIGRATION.md for migration guide.'
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Main content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header
            onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
            title=""
            subtitle=""
          />
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}