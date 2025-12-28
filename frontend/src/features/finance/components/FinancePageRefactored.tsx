/**
 * FinancePageRefactored Component
 *
 * 财务中心页面 - 重构版本 (使用拆分后的子组件)
 * Route: /finance
 * SoT 对齐: LEDGER_SOT.md v1.1, BUSINESS_RULES.md v3.2
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { DollarSign, RefreshCw, Plus } from 'lucide-react';
import { FinanceOverviewCards } from './FinanceOverviewCards';
import { FinanceTrendChart } from './FinanceTrendChart';
import { FinanceTodoList } from './FinanceTodoList';
import { FinanceTransactions } from './FinanceTransactions';
import { FinanceQuickActions } from './FinanceQuickActions';
import type {
  FinanceOverview,
  TrendDataPoint,
  PlatformSpend,
  FinanceTodo,
  LowBalanceAccount,
  Transaction,
} from '../utils/financeHelpers';

// Mock data - 财务概览
const mockOverview: FinanceOverview = {
  total_revenue: 2580000,
  total_cost: 1890000,
  total_profit: 690000,
  profit_margin: 26.7,
  pending_settlements: 156000,
  pending_topups: 85000,
};

// Mock data - 趋势数据 (最近7天)
const mockTrends: TrendDataPoint[] = [
  { date: '12-15', revenue: 320000, cost: 245000, profit: 75000 },
  { date: '12-16', revenue: 380000, cost: 278000, profit: 102000 },
  { date: '12-17', revenue: 350000, cost: 260000, profit: 90000 },
  { date: '12-18', revenue: 420000, cost: 310000, profit: 110000 },
  { date: '12-19', revenue: 390000, cost: 285000, profit: 105000 },
  { date: '12-20', revenue: 360000, cost: 268000, profit: 92000 },
  { date: '12-21', revenue: 360000, cost: 244000, profit: 116000 },
];

// Mock data - 低余额账户
const mockLowBalanceAccounts: LowBalanceAccount[] = [
  { id: 1, name: '巨量引擎-主账户', platform: '巨量引擎', balance: 5200, status: 'critical' },
  { id: 2, name: '腾讯广告-品牌号', platform: '腾讯广告', balance: 12800, status: 'low' },
  { id: 3, name: '快手磁力-效果号', platform: '快手', balance: 18500, status: 'low' },
];

// Mock data - 待办事项
const mockTodos: FinanceTodo[] = [
  { id: 1, type: 'topup', title: '充值申请待审批', amount: 50000, priority: 'high', created_at: '2024-12-21 09:30' },
  { id: 2, type: 'settlement', title: '供应商结算待处理', amount: 86000, priority: 'high', created_at: '2024-12-21 08:15' },
  { id: 3, type: 'reconciliation', title: '日报对账待确认', amount: 125000, priority: 'medium', created_at: '2024-12-20 17:00' },
  { id: 4, type: 'alert', title: '账户余额预警', priority: 'high', created_at: '2024-12-21 10:00' },
];

// Mock data - 最近交易
const mockTransactions: Transaction[] = [
  { id: 1, type: 'topup', account_name: '巨量引擎-主账户', amount: 100000, status: '已完成', created_at: '2024-12-21 10:30' },
  { id: 2, type: 'consume', account_name: '腾讯广告-品牌号', amount: -28500, status: '已扣费', created_at: '2024-12-21 09:45' },
  { id: 3, type: 'topup', account_name: '快手磁力-效果号', amount: 50000, status: '审批中', created_at: '2024-12-21 09:00' },
  { id: 4, type: 'settlement', account_name: '供应商A', amount: -45000, status: '已结算', created_at: '2024-12-20 18:00' },
  { id: 5, type: 'consume', account_name: '巨量引擎-主账户', amount: -32100, status: '已扣费', created_at: '2024-12-20 16:30' },
];

// Mock data - 平台消耗占比
const mockPlatformSpend: PlatformSpend[] = [
  { platform: '巨量引擎', spend: 890000, percentage: 47.1, trend: 'up' },
  { platform: '腾讯广告', spend: 560000, percentage: 29.6, trend: 'stable' },
  { platform: '快手磁力', spend: 320000, percentage: 16.9, trend: 'up' },
  { platform: '其他', spend: 120000, percentage: 6.4, trend: 'down' },
];

export function FinancePageRefactored() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="space-y-6" data-testid="finance-page">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-100">
            <DollarSign className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">财务中心</h1>
            <p className="text-sm text-gray-500">财务概览、账户余额和资金管理</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Link href="/topups">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              申请充值
            </Button>
          </Link>
        </div>
      </div>

      {/* Overview Cards */}
      <FinanceOverviewCards overview={mockOverview} />

      {/* Trend Chart + Platform Spend */}
      <FinanceTrendChart trendData={mockTrends} platformSpend={mockPlatformSpend} />

      {/* Todo List + Low Balance Alerts */}
      <FinanceTodoList todos={mockTodos} lowBalanceAccounts={mockLowBalanceAccounts} />

      {/* Recent Transactions */}
      <FinanceTransactions transactions={mockTransactions} />

      {/* Quick Actions */}
      <FinanceQuickActions />
    </div>
  );
}

export default FinancePageRefactored;
