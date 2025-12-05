/**
 * Dashboard 资金概览组件
 * 
 * 功能：
 * - 展示总余额、可用余额
 * - 待审核充值信息
 * - 层级感强的卡片布局
 * - 可选：微型图表或进度条
 */

'use client';

import React from 'react';
import { Wallet, AlertCircle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { FundsOverview } from '../types';

interface DashboardFundsOverviewProps {
  data: FundsOverview;
  className?: string;
  onTopupClick?: () => void;
}

export function DashboardFundsOverview({
  data,
  className,
  onTopupClick
}: DashboardFundsOverviewProps) {
  const availablePercentage =
    data.totalBalance > 0
      ? (data.availableBalance / data.totalBalance) * 100
      : 0;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <Card className={cn('rounded-lg border-border-default bg-card-bg', className)}>
      <CardHeader className="pb-4">
        <CardTitle className="text-base flex items-center gap-2 text-text-strong">
          <Wallet className="w-4 h-4 text-accent" />
          资金池概览
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 总余额卡片 */}
        <div className="p-4 bg-shell border border-border-default rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-subtle font-medium">总余额</span>
            <TrendingUp className="w-4 h-4 text-success" />
          </div>
          <div className="text-2xl font-bold text-text-strong mb-1">
            {formatCurrency(data.totalBalance)}
          </div>
          <div className="text-xs text-text-muted">
            可用余额：{formatCurrency(data.availableBalance)}
          </div>
          {/* 可用余额进度条 */}
          <div className="mt-2">
            <Progress
              value={availablePercentage}
              className="h-1 bg-border-default"
            />
            <div className="text-[10px] text-text-subtle mt-1">
              可用率：{availablePercentage.toFixed(1)}%
            </div>
          </div>
        </div>

        {/* 待审核充值卡片 */}
        <div className="p-4 bg-shell border border-border-default rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-text-subtle font-medium">待审核充值</span>
            <AlertCircle className="w-4 h-4 text-warning" />
          </div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className="text-xl font-bold text-warning">
              {data.pendingTopups.count}
            </span>
            <span className="text-xs text-text-muted">笔</span>
          </div>
          <div className="text-xs text-text-muted">
            总金额：{formatCurrency(data.pendingTopups.totalAmount)}
          </div>
          {onTopupClick && (
            <Button
              size="sm"
              variant="outline"
              onClick={onTopupClick}
              className="w-full mt-3 text-xs border-border-muted text-text-body hover:bg-elevated hover:text-text-strong"
            >
              查看详情
            </Button>
          )}
        </div>

        {/* 最近交易（可选） */}
        {data.recentTransactions && data.recentTransactions.length > 0 && (
          <div className="pt-3 border-t border-border-default">
            <div className="text-xs text-text-subtle font-medium mb-2">最近交易</div>
            <div className="space-y-1.5">
              {data.recentTransactions.slice(0, 3).map((tx) => (
                <div
                  key={tx.id}
                  className="flex items-center justify-between text-xs py-1"
                >
                  <span className="text-text-muted">{tx.type}</span>
                  <span
                    className={cn(
                      'font-medium',
                      tx.amount > 0
                        ? 'text-success'
                        : 'text-danger'
                    )}
                  >
                    {tx.amount > 0 ? '+' : ''}
                    {formatCurrency(Math.abs(tx.amount))}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

