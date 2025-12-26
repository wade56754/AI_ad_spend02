/**
 * ProfitTrendChart - 利润趋势图
 *
 * 显示按日/周/月聚合的收入、成本、利润趋势
 *
 * @module features/finance/components/ProfitAnalysis
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TrendSeriesItem, TrendGranularity } from '../../types/finance.types';

interface ProfitTrendChartProps {
  granularity: TrendGranularity;
  series: TrendSeriesItem[];
}

const GRANULARITY_LABELS: Record<TrendGranularity, string> = {
  day: '按日',
  week: '按周',
  month: '按月',
};

export function ProfitTrendChart({ granularity, series }: ProfitTrendChartProps) {
  const formatCurrency = (value: number) => `$${(value / 1000).toFixed(0)}k`;

  // 找出最大值用于计算比例
  const maxValue = Math.max(
    ...series.flatMap((s) => [s.revenue, s.cost]),
    1
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          利润趋势 ({GRANULARITY_LABELS[granularity]})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {series.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">暂无数据</div>
        ) : (
          <div className="space-y-4">
            {/* 简单的条形图表示 */}
            {series.map((item) => (
              <div key={item.period} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{item.period}</span>
                  <div className="flex gap-4">
                    <span className="text-green-600">收入: {formatCurrency(item.revenue)}</span>
                    <span className="text-blue-600">成本: {formatCurrency(item.cost)}</span>
                    <span className={item.profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                      利润: {formatCurrency(item.profit)}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1 h-4">
                  {/* 收入条 */}
                  <div
                    className="bg-green-500 rounded-sm"
                    style={{ width: `${(item.revenue / maxValue) * 50}%` }}
                  />
                  {/* 成本条 */}
                  <div
                    className="bg-blue-500 rounded-sm"
                    style={{ width: `${(item.cost / maxValue) * 50}%` }}
                  />
                </div>
              </div>
            ))}

            {/* 图例 */}
            <div className="flex justify-center gap-6 pt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-sm" />
                <span>收入</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-sm" />
                <span>成本</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
