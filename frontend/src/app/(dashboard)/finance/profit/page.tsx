/**
 * Profit Analysis Route Page (V2)
 *
 * Route: /finance/profit
 *
 * SoT 对齐:
 * - MASTER.md v4.4 §4.5.5: 利润计算规则
 * - A3-project-pnl-backend.md: 模块规格书
 *
 * 权限:
 * - ceo: 全部功能，全公司数据
 * - project_owner: 全部功能，自己负责的项目
 * - finance: 只读，全公司数据
 * - admin: 只读，全公司数据
 * - supervisor/pitcher/account_manager: 禁止访问
 */

import { ProfitAnalysisPage } from '@/features/finance';

export const metadata = {
  title: '项目盈亏 | AI 广告投放系统',
  description: '项目收入、成本、利润分析',
};

export default function ProfitAnalysisRoute() {
  return <ProfitAnalysisPage />;
}
