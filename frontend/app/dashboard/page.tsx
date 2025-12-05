/**
 * Dashboard 首页
 *
 * 职责：
 * - 页面级外壳（PageContainer）
 * - 渲染 DashboardShell 模块组件
 *
 * @see FRONTEND_STYLE_GUIDE v2.3 - Page 规范
 */

'use client';

import PageContainer from '@/components/layout/page-container';
import { DashboardShell } from '@/modules/dashboard';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-shell text-text-body antialiased">
      <PageContainer>
        <DashboardShell />
      </PageContainer>
    </div>
  );
}
