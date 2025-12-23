/**
 * Ad Accounts Page Component - v3.0
 *
 * Main page for ad account management
 * SoT 对齐: STATE_MACHINE.md v2.6 Section 7
 * UI 对齐: UI_DESIGN_SYSTEM.md v2.1
 */

'use client';

import { CreditCard } from 'lucide-react';
import { AdAccountsTable } from './AdAccountsTable';

export function AdAccountsPage() {
  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header - v3.0 白色卡片头部 */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100">
              <CreditCard className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">广告账户</h1>
              <p className="text-sm text-gray-500">管理广告投放账户及状态</p>
            </div>
          </div>
        </div>

        {/* Table Container */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <AdAccountsTable />
        </div>
      </div>
    </div>
  );
}
