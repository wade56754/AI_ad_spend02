/**
 * Suppliers Page Route
 *
 * Route: /suppliers
 * SoT 对齐: DATA_SCHEMA.md v5.2
 */

import { SuppliersPage } from '@/modules/suppliers';

export const metadata = {
  title: '供应商管理 | AI 广告投放系统',
  description: '管理户商信息、账户关联和财务数据',
};

export default function SuppliersRoute() {
  return <SuppliersPage />;
}
