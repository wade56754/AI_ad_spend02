/**
 * FinanceOverviewCards Component
 *
 * 财务概览 KPI 卡片 - 从 FinancePage.tsx 提取
 * v3.0 去边框+投影设计
 */

'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Clock,
  PieChart,
  Wallet,
} from 'lucide-react';
import { formatMoney, type FinanceOverview } from '../utils/financeHelpers';

interface FinanceOverviewCardsProps {
  overview: FinanceOverview;
  className?: string;
}

export function FinanceOverviewCards({ overview, className }: FinanceOverviewCardsProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 ${className || ''}`} data-testid="finance-overview-cards">
      {/* 本月收入 */}
      <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月收入</p>
              <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(overview.total_revenue)}</p>
              <div className="flex items-center text-green-600 text-sm">
                <ArrowUpRight className="h-4 w-4" />
                <span>+12.5% 较上月</span>
              </div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50">
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 本月成本 */}
      <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月成本</p>
              <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatMoney(overview.total_cost)}</p>
              <div className="flex items-center text-red-600 text-sm">
                <ArrowUpRight className="h-4 w-4" />
                <span>+8.2% 较上月</span>
              </div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50">
              <TrendingDown className="h-5 w-5 text-red-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 本月利润 */}
      <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">本月利润</p>
              <p className="text-3xl font-bold text-green-600 tabular-nums">{formatMoney(overview.total_profit)}</p>
              <div className="flex items-center text-gray-500 text-sm">
                <span>利润率 {overview.profit_margin}%</span>
              </div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
              <PieChart className="h-5 w-5 text-blue-600" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 待结算金额 */}
      <Card className="shadow-sm hover:shadow-md transition-shadow border-0">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">待结算金额</p>
              <p className="text-3xl font-bold text-amber-600 tabular-nums">{formatMoney(overview.pending_settlements)}</p>
              <div className="flex items-center text-amber-600 text-sm">
                <Clock className="h-4 w-4 mr-1" />
                <span>3 笔待处理</span>
              </div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50">
              <Wallet className="h-5 w-5 text-amber-600" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default FinanceOverviewCards;
