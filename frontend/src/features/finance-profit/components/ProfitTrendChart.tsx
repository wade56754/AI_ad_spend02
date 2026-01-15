/**
 * ProfitTrendChart Component
 *
 * Displays profit trend using recharts
 * SoT 对齐: BUSINESS_RULES.md v3.1
 */

'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { Button } from '@/components/ui/button';
import type { ProfitTrendResponse, TrendGranularity } from '../types';
import { TREND_GRANULARITY_CONFIG } from '../types';

interface ProfitTrendChartProps {
  data: ProfitTrendResponse | undefined;
  loading?: boolean;
  granularity: TrendGranularity;
  onGranularityChange?: (granularity: TrendGranularity) => void;
}

export function ProfitTrendChart({
  data,
  loading = false,
  granularity,
  onGranularityChange,
}: ProfitTrendChartProps) {
  const formatCurrency = (value: number) => {
    if (value >= 10000) {
      return `¥${(value / 10000).toFixed(1)}万`;
    }
    return `¥${value.toFixed(0)}`;
  };

  const formatTooltipValue = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const chartData =
    data?.items.map((item) => ({
      period: item.period,
      profit: item.total_profit,
      revenue: item.total_revenue,
      cost: item.total_cost,
      margin: item.profit_margin,
      changeRate: item.profit_change_rate,
    })) || [];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4 animate-pulse"></div>
        <div className="h-64 bg-gray-100 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">利润趋势</h3>
        {onGranularityChange && (
          <div className="flex gap-2">
            {Object.entries(TREND_GRANULARITY_CONFIG).map(([key, config]) => (
              <Button
                key={key}
                onClick={() => onGranularityChange(key as TrendGranularity)}
                variant="ghost"
                size="sm"
                className={
                  granularity === key
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              >
                {config.label}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Statistics Summary */}
      {data && (
        <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <div className="text-sm text-gray-500">平均利润</div>
            <div className="text-lg font-semibold text-gray-900">
              {formatTooltipValue(data.avg_profit)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">最高利润</div>
            <div className="text-lg font-semibold text-green-600">
              {formatTooltipValue(data.max_profit)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">最低利润</div>
            <div className="text-lg font-semibold text-red-600">
              {formatTooltipValue(data.min_profit)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">波动率</div>
            <div className="text-lg font-semibold text-gray-900">
              {data.profit_volatility.toFixed(2)}%
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-80">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="period" tick={{ fontSize: 12 }} tickLine={false} />
              <YAxis
                tickFormatter={formatCurrency}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(value: number | undefined, name: string | undefined) => [
                  formatTooltipValue(value ?? 0),
                  name === 'profit' ? '利润' : name === 'revenue' ? '收入' : '成本',
                ]}
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Legend
                formatter={(value) => {
                  const labels: Record<string, string> = {
                    profit: '利润',
                    revenue: '收入',
                    cost: '成本',
                  };
                  return labels[value] || value;
                }}
              />
              <Area
                type="monotone"
                dataKey="revenue"
                stroke="#10b981"
                fill="url(#revenueGradient)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="profit"
                stroke="#3b82f6"
                fill="url(#profitGradient)"
                strokeWidth={2}
              />
              <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-500">暂无趋势数据</div>
        )}
      </div>
    </div>
  );
}

export default ProfitTrendChart;
