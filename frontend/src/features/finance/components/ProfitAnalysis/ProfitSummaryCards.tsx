/**
 * ProfitSummaryCards - 盈亏概览统计卡片
 *
 * 显示 4 个核心盈亏指标：总收入、总成本、总利润、平均利润率
 *
 * @module features/finance/components/ProfitAnalysis
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon, DollarSign, TrendingDown, Wallet, Percent } from 'lucide-react';
import type { ProfitSummary, ProfitChanges, ProfitBenchmarks } from '../../types/finance.types';

interface ProfitSummaryCardsProps {
  data: {
    summary: ProfitSummary;
    changes: ProfitChanges;
    benchmarks: ProfitBenchmarks;
  };
  currency?: string;
}

export function ProfitSummaryCards({ data, currency = 'USD' }: ProfitSummaryCardsProps) {
  const { summary, changes, benchmarks } = data;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  const cards = [
    {
      title: '总收入',
      value: formatCurrency(summary.total_revenue),
      subtitle: `${summary.total_conversions}个粉`,
      change: changes.revenue_change_pct,
      icon: DollarSign,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
    },
    {
      title: '总成本',
      value: formatCurrency(summary.total_cost),
      subtitle: `含费${formatCurrency(summary.total_fee)}`,
      icon: TrendingDown,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
    },
    {
      title: '总利润',
      value: formatCurrency(summary.total_profit),
      change: changes.profit_change_pct,
      subtitle: 'vs上月',
      icon: Wallet,
      iconBg: summary.total_profit >= 0 ? 'bg-green-100' : 'bg-red-100',
      iconColor: summary.total_profit >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      title: '平均利润率',
      value: formatPercent(summary.avg_profit_rate),
      subtitle: `行业${formatPercent(benchmarks.industry_avg_profit_rate)}`,
      isAboveBenchmark: summary.avg_profit_rate >= benchmarks.industry_avg_profit_rate,
      icon: Percent,
      iconBg: summary.avg_profit_rate >= benchmarks.industry_avg_profit_rate ? 'bg-green-100' : 'bg-amber-100',
      iconColor: summary.avg_profit_rate >= benchmarks.industry_avg_profit_rate ? 'text-green-600' : 'text-amber-600',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <div className={`p-2 rounded-full ${card.iconBg}`}>
                <Icon className={`h-4 w-4 ${card.iconColor}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <div className="flex items-center text-xs text-muted-foreground mt-1">
                {card.change !== undefined && card.change !== null && (
                  <>
                    {card.change >= 0 ? (
                      <ArrowUpIcon className="mr-1 h-3 w-3 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="mr-1 h-3 w-3 text-red-500" />
                    )}
                    <span className={card.change >= 0 ? 'text-green-500' : 'text-red-500'}>
                      {Math.abs(card.change).toFixed(1)}%
                    </span>
                    <span className="ml-1">{card.subtitle}</span>
                  </>
                )}
                {(card.change === undefined || card.change === null) && (
                  <span>{card.subtitle}</span>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
