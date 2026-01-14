/**
 * ProfitSummaryCards - 盈亏概览统计卡片
 *
 * 显示 4 个核心盈亏指标：总收入、总成本、总利润、平均利润率
 *
 * UI 设计规范 (财务模块最佳实践):
 * - 4 列响应式网格: grid gap-4 md:grid-cols-2 lg:grid-cols-4
 * - 卡片四要素: 标题 + 数值 + 变化率/基准对比 + 图标
 * - 颜色语义: 绿色收入、蓝色成本、动态利润色、动态利润率色
 * - 数值格式: formatCurrency (金额) + formatPercent (百分比)
 * - 基准对比: 与行业平均值对比
 *
 * SoT: BR-PROFIT.md v1.3 §BR-PROFIT-001/002/003/004/005 (利润公式)
 * 修复: 2026-01-12 货币默认值 USD→CNY
 *
 * @module features/finance/components/ProfitAnalysis
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowUpIcon, ArrowDownIcon, DollarSign, TrendingDown, Wallet, Percent } from 'lucide-react';
import type { ProfitSummary, ProfitChanges, ProfitBenchmarks } from '../../types/finance.types';
import { formatCurrency, formatPercent } from '../../utils/financeHelpers';

interface ProfitSummaryCardsProps {
  data: {
    summary: ProfitSummary;
    changes: ProfitChanges;
    benchmarks: ProfitBenchmarks;
  };
  currency?: 'CNY' | 'USD';
}

export function ProfitSummaryCards({ data, currency = 'CNY' }: ProfitSummaryCardsProps) {
  // 防御性检查：为缺失的数据提供默认值
  const summary = data?.summary ?? {
    total_revenue: 0,
    total_cost: 0,
    total_profit: 0,
    total_conversions: 0,
    avg_profit_rate: 0,
    total_fee: 0,
  };
  const changes = data?.changes ?? { revenue_change_pct: null, profit_change_pct: null };
  const benchmarks = data?.benchmarks ?? { industry_avg_profit_rate: 0.15, company_target_profit_rate: 0.20 };

  // 创建带货币参数的格式化函数
  const fmtCurrency = (value: number) => formatCurrency(value, currency);
  const fmtPercent = (value: number) => formatPercent(value);

  // 判断变化率是否有效（非 NaN、非 Infinity、非极端值）
  // 新增：当当前值为 0 但变化率非 0 时也视为无效（数学上无意义）
  const isValidChange = (change: number | null | undefined, currentValue?: number): boolean => {
    if (change === null || change === undefined) return false;
    if (!Number.isFinite(change)) return false;
    // 超过 1000% 的变化率视为无效（可能是除以 0 或极端情况）
    if (Math.abs(change) > 1000) return false;
    // 当前值为 0 但变化率非零时视为无效（0 到 0 的变化率应为 0%，不应是其他值）
    if (currentValue === 0 && change !== 0) return false;
    return true;
  };

  const cards = [
    {
      title: '总收入',
      value: fmtCurrency(summary.total_revenue),
      rawValue: summary.total_revenue, // 用于判断变化率有效性
      subtitle: `${summary.total_conversions}个粉`,
      change: changes.revenue_change_pct,
      icon: DollarSign,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
    },
    {
      title: '总成本',
      value: fmtCurrency(summary.total_cost),
      subtitle: `含费${fmtCurrency(summary.total_fee)}`,
      icon: TrendingDown,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      showActualBadge: true, // P0-3: 标注为实际消耗
    },
    {
      title: '总利润',
      value: fmtCurrency(summary.total_profit),
      rawValue: summary.total_profit, // 用于判断变化率有效性
      change: changes.profit_change_pct,
      subtitle: 'vs上月',
      icon: Wallet,
      iconBg: summary.total_profit >= 0 ? 'bg-green-100' : 'bg-red-100',
      iconColor: summary.total_profit >= 0 ? 'text-green-600' : 'text-red-600',
    },
    {
      title: '平均利润率',
      value: fmtPercent(summary.avg_profit_rate),
      subtitle: `行业${fmtPercent(benchmarks.industry_avg_profit_rate)}`,
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
                {isValidChange(card.change, 'rawValue' in card ? card.rawValue : undefined) && (
                  <>
                    {card.change! >= 0 ? (
                      <ArrowUpIcon className="mr-1 h-3 w-3 text-green-500" />
                    ) : (
                      <ArrowDownIcon className="mr-1 h-3 w-3 text-red-500" />
                    )}
                    <span className={card.change! >= 0 ? 'text-green-500' : 'text-red-500'}>
                      {Math.abs(card.change!).toFixed(1)}%
                    </span>
                    <span className="ml-1">{card.subtitle}</span>
                  </>
                )}
                {card.change !== undefined && !isValidChange(card.change, 'rawValue' in card ? card.rawValue : undefined) && (
                  <>
                    <span className="text-gray-400">-</span>
                    <span className="ml-1">{card.subtitle}</span>
                  </>
                )}
                {card.change === undefined && !('showActualBadge' in card && card.showActualBadge) && (
                  <span>{card.subtitle}</span>
                )}
                {/* P0-3: 总成本显示实际消耗标签 */}
                {'showActualBadge' in card && card.showActualBadge && (
                  <div className="flex items-center gap-1">
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                      实际消耗
                    </span>
                    <span className="text-gray-400">{card.subtitle}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
