/**
 * Dashboard Home Page
 *
 * Route: / (dashboard root)
 */

import { DashboardPage } from '@/features/dashboard';

export const metadata = {
  title: '仪表盘 | AI 广告投放系统',
  description: '系统数据概览和关键指标',
};

export default function DashboardRoute() {
  return <DashboardPage />;
}
