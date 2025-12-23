/**
 * Ledger Page Component - v3.0
 *
 * Main page for ledger management
 * SoT: LEDGER_SOT.md v1.1
 * UI 对齐: UI_DESIGN_SYSTEM.md v2.1
 */

'use client';

import { BookOpen } from 'lucide-react';
import { LedgerTable } from './LedgerTable';

export function LedgerPage() {
  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header - v3.0 白色卡片头部 */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100">
              <BookOpen className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">财务总账</h1>
              <p className="text-sm text-gray-500">查看账户收支明细及余额变动</p>
            </div>
          </div>
        </div>

        {/* Table Container */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <LedgerTable />
        </div>
      </div>
    </div>
  );
}
