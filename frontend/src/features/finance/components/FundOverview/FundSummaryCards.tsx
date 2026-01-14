/**
 * FundSummaryCards - 资金概览统计卡片
 *
 * 显示 4 个核心资金指标：本月收款、本月支出、应收未收、可用余额
 *
 * UI 设计规范 (财务模块最佳实践):
 * - 4 列响应式网格: grid gap-4 md:grid-cols-2 lg:grid-cols-4
 * - 卡片四要素: 标题 + 数值 + 变化率 + 图标
 * - 颜色语义: 绿色收入、蓝色支出、琥珀待处理、紫色余额
 * - 数值格式: text-2xl font-bold + formatCurrency
 * - 变化率: 正数绿色、负数红色 + Arrow 图标
 *
 * SoT: BR-FIN.md v1.1 §BR-FIN-006 (可用资金公式)
 *
 * @module features/finance/components/FundOverview
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon, DollarSign, TrendingUp, AlertCircle, Wallet } from 'lucide-react';
import type { FundSummary, FundChanges } from '../../types/finance.types';
import { formatCurrency } from '../../utils/financeHelpers';

interface FundSummaryCardsProps {
  data: {
    summary: FundSummary;
    changes: FundChanges;
  };
  currency?: 'CNY' | 'USD';
}

export function FundSummaryCards({ data, currency = 'USD' }: FundSummaryCardsProps) {
  // 防御性检查：为缺失的数据提供默认值
  const summary = data?.summary ?? {
    total_income: 0,
    total_expense: 0,
    total_receivable: 0,
    total_received: 0,
    outstanding: 0,
    outstanding_count: 0,
    available_balance: 0,
    opening_balance: 0,
  };
  const changes = data?.changes ?? { income_change_pct: null, expense_change_pct: null, balance_change_pct: null };

  // 创建带货币参数的格式化函数
  const fmtCurrency = (value: number) => formatCurrency(value, currency);

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
      subtitle: '实际消耗（财务依据）',  // P0-3: 明确标注数据类型
      icon: TrendingUp,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      showBadge: true,  // P0-3: 显示数据类型标签
      badgeType: 'actual' as const,
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
              <div className="text-2xl font-bold">{fmtCurrency(card.value)}</div>
              <div className="flex items-center flex-wrap gap-1 text-xs text-muted-foreground mt-1">
                {card.change !== undefined && card.change !== null && (
                  <>
                    {card.change >= 0 ? (
                      <ArrowUpIcon className="h-3 w-3 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="h-3 w-3 text-red-500" />
                    )}
                    <span className={card.change >= 0 ? 'text-green-500' : 'text-red-500'}>
                      {Math.abs(card.change).toFixed(1)}%
                    </span>
                  </>
                )}
                {/* P0-3: 显示数据类型标签 */}
                {'showBadge' in card && card.showBadge && (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                    实际消耗
                  </span>
                )}
                {!('showBadge' in card && card.showBadge) && (
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
