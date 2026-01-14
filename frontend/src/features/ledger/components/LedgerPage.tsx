/**
 * Ledger Page Component - v3.1
 *
 * Main page for ledger management with transaction entry capability
 *
 * SoT References:
 * - LEDGER_SOT.md v1.1 (Double-entry bookkeeping)
 * - BR-FIN.md v1.1 (Financial business rules)
 * - MASTER.md v4.9 §2.4 (Role permissions: admin, finance)
 *
 * UI 对齐: UI_DESIGN_SYSTEM.md v2.1
 */

'use client';

import { useState } from 'react';
import { BookOpen, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/api';
import { LedgerTable } from './LedgerTable';
import { TransactionEntryForm } from './TransactionEntryForm';
import { AdjustmentForm } from './AdjustmentForm';

export function LedgerPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const queryClient = useQueryClient();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
    setIsRefreshing(false);
  };

  const handleTransactionSuccess = () => {
    // Refresh data after new transaction
    queryClient.invalidateQueries({ queryKey: queryKeys.ledger.all });
  };

  return (
    <div className="min-h-screen bg-gray-50 -m-6 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header - v3.1 增加操作按钮 */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100">
                <BookOpen className="h-6 w-6 text-emerald-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">财务总账</h1>
                <p className="text-sm text-gray-500">
                  查看账户收支明细及余额变动，支持手工录入交易
                </p>
              </div>
            </div>

            {/* 操作按钮区域 */}
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
                />
                刷新
              </Button>
              <AdjustmentForm onSuccess={handleTransactionSuccess} />
              <TransactionEntryForm onSuccess={handleTransactionSuccess} />
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
