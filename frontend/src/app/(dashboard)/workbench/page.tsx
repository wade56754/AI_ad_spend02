/**
 * Pitcher Workbench Page Route
 *
 * Route: /workbench
 * Task: TASK-RPT-005 - 投手工作台
 * SoT: API_SOT.md v9.0 - Daily Reports API
 *
 * Purpose: Pitcher-focused dashboard for daily report management
 * - Submit daily reports for assigned accounts
 * - View today's pending accounts
 * - Track KPIs (submissions, spend, conversions, CPL)
 * - Manage own reports (edit/delete when status allows)
 */

import { PitcherWorkbench } from '@/features/daily-reports';

export const metadata = {
  title: '投手工作台 | AI 广告投放系统',
  description: '投手日报管理工作台 - 提交日报、查看KPI、管理账户',
};

export default function WorkbenchRoute() {
  return <PitcherWorkbench />;
}
