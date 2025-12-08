/**
 * Settlements Page Route
 *
 * Route: /settlements
 * SoT 对齐: DATA_SCHEMA.md v5.2, LEDGER_SOT.md v1.1
 */

import { SettlementsPage } from '@/modules/settlements';

export const metadata = {
  title: '结算管理 | AI 广告投放系统',
  description: '管理供应商和客户结算',
};

export default function SettlementsRoute() {
  return <SettlementsPage />;
}
