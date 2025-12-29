/**
 * Spend Detail Page Route
 *
 * Route: /spend-detail
 * SoT: docs/10.module-specs/C3-spend-detail.md
 *
 * 消耗明细页面
 */

import { AdSpendPage } from '@/features/ad-spend';

export const metadata = {
  title: '消耗明细 | AI 广告投放系统',
  description: '查看广告账户消耗明细',
};

export default function SpendDetailRoute() {
  return <AdSpendPage />;
}
