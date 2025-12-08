/**
 * Reconciliation Page Component
 *
 * Main page for reconciliation management
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { ReconciliationTable } from './ReconciliationTable';

export function ReconciliationPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">对账管理</h1>
          <p className="text-muted-foreground">日报消耗数据对账及差异分析</p>
        </div>
      </div>

      <ReconciliationTable />
    </div>
  );
}
