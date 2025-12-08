/**
 * Topups Page Component
 *
 * Main page for topup request management
 * SoT: STATE_MACHINE.md v2.6 Section 7
 */

'use client';

import { TopupsTable } from './TopupsTable';

export function TopupsPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">充值管理</h1>
          <p className="text-muted-foreground">管理项目充值申请与审批</p>
        </div>
      </div>

      <TopupsTable />
    </div>
  );
}
