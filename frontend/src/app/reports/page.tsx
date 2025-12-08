/**
 * Reports Page
 *
 * Next.js app router page for /reports
 * @see backend/routers/reports.py v2.0
 */

import { ReportsPage } from '@/modules/reports';

export const metadata = {
  title: '报表中心 | AI广告代投系统',
  description: '查看仪表盘、效果报表、利润报表等多维度数据分析',
};

export default function Page() {
  return <ReportsPage />;
}
