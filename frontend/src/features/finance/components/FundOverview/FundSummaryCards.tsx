/**
 * FundSummaryCards - 资金概览统计卡片
 *
 * 显示 4 个核心资金指标：本月收款、本月支出、应收未收、可用余额
 *
 * @module features/finance/components/FundOverview
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon, DollarSign, TrendingUp, AlertCircle, Wallet } from 'lucide-react';
import type { FundSummary, FundChanges } from '../../types/finance.types';

interface FundSummaryCardsProps {
  data: {
    summary: FundSummary;
    changes: FundChanges;
  };
  currency?: string;
}

export function FundSummaryCards({ data, currency = 'USD' }: FundSummaryCardsProps) {
  const { summary, changes } = data;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const cards = [
    {
      title: '本月收款',
      value: summary.total_income,
      change: changes.income_change_pct,
      subtitle: 'vs上月',
      icon: DollarSign,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
    },
    {
      title: '本月支出',
      value: summary.total_expense,
      change: changes.expense_change_pct,
      subtitle: 'vs上月',
      icon: TrendingUp,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
    },
    {
      title: '应收未收',
      value: summary.outstanding,
      subtitle: `${summary.outstanding_count}笔待收`,
      isHighlight: summary.outstanding > 0,
      icon: AlertCircle,
      iconBg: summary.outstanding > 0 ? 'bg-amber-100' : 'bg-gray-100',
      iconColor: summary.outstanding > 0 ? 'text-amber-600' : 'text-gray-600',
    },
    {
      title: '可用余额',
      value: summary.available_balance,
      change: changes.balance_change_pct,
      subtitle: 'vs上月',
      icon: Wallet,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.title}
            className={card.isHighlight ? 'border-amber-500' : ''}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <div className={`p-2 rounded-full ${card.iconBg}`}>
                <Icon className={`h-4 w-4 ${card.iconColor}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(card.value)}</div>
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
