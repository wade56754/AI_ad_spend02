/**
 * Dashboard 趋势图表区域组件
 * 
 * 功能：
 * - 双轴组合图（消耗柱状图 + ROI 折线图）
 * - 时间范围筛选 Tabs
 * - 清晰的标题和副标题
 * - 优化的 Tooltip 信息
 */

'use client';

import React, { useState } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { TrendChartData, TimeRange } from '../types';

interface DashboardTrendSectionProps {
  data: TrendChartData[];
  className?: string;
}

const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
];

export function DashboardTrendSection({
  data,
  className
}: DashboardTrendSectionProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');

  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card-bg border border-border-default rounded-lg p-3 shadow-lg">
          <p className="text-xs text-text-muted mb-2">
            {payload[0]?.payload?.date}
          </p>
          <div className="space-y-1">
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-text-body">
                  {entry.name === 'spend' ? '消耗' : 'ROI'}:{' '}
                  <span className="font-semibold">
                    {entry.name === 'spend'
                      ? `$${entry.value.toLocaleString()}`
                      : entry.value.toFixed(2)}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={cn('rounded-lg border-border-default bg-card-bg', className)}>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <CardTitle className="text-lg font-semibold text-text-strong mb-1">
              投放效能趋势
            </CardTitle>
            <p className="text-sm text-text-muted">
              消耗金额与投资回报率对比分析
            </p>
          </div>

          {/* 时间范围筛选 Tabs */}
          <Tabs value={timeRange} onValueChange={(v) => setTimeRange(v as TimeRange)}>
            <TabsList className="bg-elevated border-border-muted">
              {TIME_RANGE_OPTIONS.map((option) => (
                <TabsTrigger
                  key={option.value}
                  value={option.value}
                  className="data-[state=active]:bg-border-muted data-[state=active]:text-text-strong text-text-muted"
                >
                  {option.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* 图例 */}
        <div className="flex gap-4 mt-3 text-xs">
          <div className="flex items-center gap-1.5 text-text-muted">
            <span className="w-2 h-2 rounded-full bg-accent" />
            消耗 ($)
          </div>
          <div className="flex items-center gap-1.5 text-text-muted">
            <span className="w-2 h-2 rounded-full bg-success" />
            ROI
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-[320px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data}>
              <defs>
                <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1e293b"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tick={{ fill: '#94a3b8' }}
              />
              <YAxis
                yAxisId="left"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `$${val}`}
                tick={{ fill: '#94a3b8' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                yAxisId="left"
                dataKey="spend"
                fill="url(#colorSpend)"
                barSize={32}
                radius={[4, 4, 0, 0]}
                name="消耗"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="roi"
                stroke="#34d399"
                strokeWidth={3}
                dot={{ r: 4, fill: '#0f172a', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#34d399' }}
                name="ROI"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

