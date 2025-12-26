/**
 * Project PnL Page Route
 *
 * Route: /project-pnl
 * SoT: docs/10.module-specs/A3-project-pnl.md
 *
 * This route is an alias for /finance/profit
 * Added to support E2E test expectations
 */

import { FinanceProfitPage } from '@/features/finance-profit';

export const metadata = {
  title: '项目盈亏 | AI 广告投放系统',
  description: '项目盈亏分析与多维度利润统计',
};

export default function ProjectPnlRoute() {
  return <FinanceProfitPage />;
}
