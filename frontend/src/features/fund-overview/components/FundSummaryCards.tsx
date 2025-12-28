/**
 * FundSummaryCards Component
 *
 * SoT: docs/10.module-specs/A2-fund-overview.md
 * SoT: MASTER.md v4.4 §6.5 页面 2 资金总览字段集
 * CodeBlock: CB-FE-002 (StatCard)
 *
 * 功能: 5 个核心资金指标卡片
 * - 累计充值
 * - 累计消耗
 * - 当前余额
 * - 应收款项
 * - 资金占用
 */

'use client';

import React from 'react';
import {
  CreditCard,
  TrendingDown,
  Wallet,
  Receipt,
  Lock,
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { StatCard } from '@/features/dashboard/components/StatCard';
import type { FundOverview } from '../types';
import { FUND_STAT_CARDS_CONFIG } from '../types';

export interface FundSummaryCardsProps {
  data: FundOverview;
  loading?: boolean;
}

/**
 * 格式化金额显示（单位：万）
 */
function formatCurrency(value: number): string {
  if (value === 0) return '¥0';
  const wan = value / 10000;
  if (Math.abs(wan) >= 1) {
    return `¥${wan.toFixed(1)} 万`;
  }
  return `¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * 指标卡片加载骨架屏
 */
function StatCardSkeleton() {
  return (
    <Card className="rounded-xl">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-12 w-12 rounded-lg" />
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
        <Skeleton className="h-9 w-32 mb-2" />
        <Skeleton className="h-4 w-20 mb-3" />
        <div className="pt-3 border-t">
          <Skeleton className="h-3 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 资金汇总卡片组件
 */
export function FundSummaryCards({ data, loading }: FundSummaryCardsProps) {
  // 图标映射
  const iconMap: Record<string, React.ReactNode> = {
    'credit-card': <CreditCard className="h-6 w-6" />,
    'trending-down': <TrendingDown className="h-6 w-6" />,
    wallet: <Wallet className="h-6 w-6" />,
    receipt: <Receipt className="h-6 w-6" />,
    lock: <Lock className="h-6 w-6" />,
  };

  // 获取指标值
  const getStatValue = (key: string): number => {
    const keyMap: Record<string, keyof FundOverview> = {
      total_topup: 'total_topup',
      total_spend: 'total_spend',
      current_balance: 'current_balance',
      total_receivable: 'total_receivable',
      fund_occupied: 'fund_occupied',
    };
    const mappedKey = keyMap[key];
    if (mappedKey && typeof data[mappedKey] === 'number') {
      return data[mappedKey] as number;
    }
    return 0;
  };

  // 获取变化值
  const getChangeValue = (key: string): number | null => {
    const changeMap: Record<string, keyof FundOverview> = {
      total_topup: 'topup_change',
      total_spend: 'spend_change',
      current_balance: 'balance_change',
    };
    const mappedKey = changeMap[key];
    if (mappedKey) {
      return data[mappedKey] as number | null;
    }
    return null;
  };

  // 获取副信息
  const getSubInfo = (key: string): string | undefined => {
    if (key === 'total_receivable') {
      return `${data.pending_receivable_count} 笔待收`;
    }
    if (key === 'fund_occupied') {
      return `占用率 ${data.occupy_rate.toFixed(1)}%`;
    }
    return undefined;
  };

  if (loading) {
    return (
      <section>
        <h2 className="text-lg font-semibold text-foreground mb-4">核心指标</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
      </section>
    );
  }

  return (
    <section>
      <h2 className="text-lg font-semibold text-foreground mb-4">核心指标</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {FUND_STAT_CARDS_CONFIG.map((config) => (
          <StatCard
            key={config.key}
            title={config.title}
            value={formatCurrency(getStatValue(config.key))}
            change={getChangeValue(config.key)}
            target={getSubInfo(config.key)}
            icon={iconMap[config.icon]}
            color={config.color}
            testId={`fund-stat-${config.key}`}
          />
        ))}
      </div>
    </section>
  );
}

export default FundSummaryCards;
