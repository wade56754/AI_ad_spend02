/**
 * Dashboard Home Page
 *
 * Route: / (dashboard root)
 *
 * CEO Dashboard V3 - 重构版本
 * Core Formula: Gross Profit = Revenue - Cost (No handling fee!)
 */

import { CEODashboardV3 } from '@/features/dashboard/components/CEODashboardV3';

export const metadata = {
  title: 'CEO 驾驶舱 | AI 广告投放系统',
  description: '公司盈亏概览和关键指标',
};

export default function DashboardRoute() {
  return <CEODashboardV3 />;
}
