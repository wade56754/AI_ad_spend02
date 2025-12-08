/**
 * Daily Reports Page Component
 *
 * Main page for daily report management
 * SoT: STATE_MACHINE.md v2.6 Section 8
 */

'use client';

import { DailyReportsTable } from './DailyReportsTable';

export function DailyReportsPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">日报管理</h1>
          <p className="text-muted-foreground">管理广告消耗日报数据及审批流程</p>
        </div>
      </div>

      <DailyReportsTable />
    </div>
  );
}
