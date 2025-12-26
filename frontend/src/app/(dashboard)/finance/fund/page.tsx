/**
 * Fund Overview Route Page (V2)
 *
 * Route: /finance/fund
 *
 * SoT 对齐:
 * - MASTER.md v4.4 §4.5.5: 资金口径定义
 * - MASTER.md v4.4 §6.5: 页面 2 资金总览字段集
 * - A2-fund-overview-backend.md: 模块规格书
 *
 * 权限:
 * - ceo: 全部功能，全公司数据
 * - finance: 全部功能，全公司数据
 * - project_owner: 只读，自己负责的项目
 * - account_manager: 只读，账户余额部分
 * - admin: 只读，全公司数据
 * - supervisor/pitcher: 禁止访问
 */

import { FundOverviewPage } from '@/features/finance';

export const metadata = {
  title: '资金总览 | AI 广告投放系统',
  description: '公司资金流向全景：收款、支出、应收未收、余额、资金分布',
};

export default function Page() {
  return <FundOverviewPage />;
}
