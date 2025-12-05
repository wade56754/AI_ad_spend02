/**
 * FinanceKpiRow - 财务模块 KPI 指标卡片
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Wallet,
  TrendingUp,
  Clock,
  CheckCircle,
  ArrowUpRight,
} from 'lucide-react';
import type { FinancialSummary } from '../types';

interface FinanceKpiRowProps {
  summary: FinancialSummary;
  pendingCount: number;
  loading?: boolean;
}

export function FinanceKpiRow({
  summary,
  pendingCount,
  loading = false,
}: FinanceKpiRowProps) {
  const growthRate =
    ((summary.this_month_spending - summary.last_month_spending) /
      summary.last_month_spending) *
    100;

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-32 bg-muted animate-pulse rounded mb-2" />
              <div className="h-3 w-24 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-text-muted">
            账户总余额
          </CardTitle>
          <Wallet className="h-4 w-4 text-text-muted" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-text-strong">
            ¥{summary.total_balance.toLocaleString()}
          </div>
          <p className="text-xs text-text-muted">
            本月已支出 ¥{summary.this_month_spending.toLocaleString()}
          </p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-text-muted">
            本月支出
          </CardTitle>
          <TrendingUp className="h-4 w-4 text-text-muted" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-text-strong">
            ¥{summary.this_month_spending.toLocaleString()}
          </div>
          <p className="text-xs text-success flex items-center">
            <ArrowUpRight className="w-3 h-3 mr-1" />
            比上月增长 {growthRate.toFixed(1)}%
          </p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-text-muted">
            待审批充值
          </CardTitle>
          <Clock className="h-4 w-4 text-text-muted" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-text-strong">
            ¥{summary.pending_topups.toLocaleString()}
          </div>
          <p className="text-xs text-text-muted">{pendingCount} 个申请待审核</p>
        </CardContent>
      </Card>

      <Card className="bg-card border-border">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-text-muted">
            审批效率
          </CardTitle>
          <CheckCircle className="h-4 w-4 text-text-muted" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-text-strong">
            {summary.success_rate}%
          </div>
          <p className="text-xs text-text-muted">
            平均审批时间 {summary.average_approval_time} 小时
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
