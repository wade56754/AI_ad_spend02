/**
 * Fund Overview Route Page
 *
 * Route: /fund
 *
 * SoT 对齐:
 * - MASTER.md v4.4 §4.5.5: 资金口径定义
 * - MASTER.md v4.4 §6.5: 页面 2 资金总览字段集
 * - A2-fund-overview.md: 模块规格书
 *
 * 权限:
 * - ceo: 全部功能，全公司数据
 * - finance: 全部功能，全公司数据
 * - project_owner: 只读，自己负责的项目
 * - account_manager: 只读，账户余额部分
 * - admin: 只读，全公司数据
 * - supervisor/pitcher: 禁止访问
 */

import { FundOverviewPage } from '@/features/fund-overview';

export const metadata = {
  title: '资金总览 | AI 广告投放系统',
  description: '一眼看清公司资金全貌，掌握资金流向和回款情况',
};

export default function Page() {
  return <FundOverviewPage />;
}
