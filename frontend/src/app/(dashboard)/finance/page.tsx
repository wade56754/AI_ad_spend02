/**
 * Finance Overview Route Page
 *
 * Route: /finance
 * SoT 对齐: LEDGER_SOT.md v1.1
 */

import { FinancePage } from '@/features/finance';

export const metadata = {
  title: '财务中心 | AI 广告投放系统',
  description: '财务概览、账户余额和资金管理',
};

export default function Page() {
  return <FinancePage />;
}
