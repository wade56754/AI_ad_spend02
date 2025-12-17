/**
 * Ledger Page Component
 *
 * Main page for ledger management
 * SoT: LEDGER_SOT.md v1.1
 */

'use client';

import { LedgerTable } from './LedgerTable';

export function LedgerPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">财务总账</h1>
          <p className="text-muted-foreground">查看账户收支明细及余额变动</p>
        </div>
      </div>

      <LedgerTable />
    </div>
  );
}
