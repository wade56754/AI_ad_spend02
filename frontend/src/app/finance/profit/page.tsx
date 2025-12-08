/**
 * Finance Profit Page Route
 *
 * Route: /finance/profit
 * SoT 对齐: BUSINESS_RULES.md v3.1
 */

import { FinanceProfitPage } from '@/modules/finance-profit';

export const metadata = {
  title: '利润分析 | AI 广告投放系统',
  description: '查看利润概览、趋势分析和多维度利润统计',
};

export default function FinanceProfitRoute() {
  return <FinanceProfitPage />;
}
