'use client';

import { AppLayout } from '@/components/dashboard/AppLayout';

/**
 * 仪表板页面布局
 * 包含侧边栏和顶部导航
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppLayout>{children}</AppLayout>;
}
