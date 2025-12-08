/**
 * Ad Accounts Page Component
 *
 * Main page for ad account management
 * SoT 对齐: STATE_MACHINE.md v2.6 Section 7
 */

'use client';

import { AdAccountsTable } from './AdAccountsTable';

export function AdAccountsPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">广告账户</h1>
          <p className="text-muted-foreground">管理广告投放账户及状态</p>
        </div>
      </div>

      <AdAccountsTable />
    </div>
  );
}
