/**
 * MainTrendChart Component
 *
 * 主趋势图 - 多指标合并展示
 * - 支持切换显示不同指标(消耗/收入/利润)
 * - 包含自动总结文案区域
 * - 查看明细按钮
 *
 * Based on UI_DESIGN_SYSTEM.md v2.0
 */

'use client';

import React, { useMemo } from 'react';
import Link from 'next/link';
import { ExternalLink, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { cn } from '@/lib/utils';

export type MetricType = 'spend' | 'revenue' | 'profit' | 'conversions';

export interface TrendDataPoint {
  date: string;
  spend?: number;
  revenue?: number;
  profit?: number;
  conversions?: number;
}

interface MainTrendChartProps {
  data: TrendDataPoint[];
  activeMetric: MetricType;
  onMetricChange?: (metric: MetricType) => void;
  summary?: string; // AI 生成的总结文案
  className?: string;
}

const METRIC_CONFIG: Record<
  MetricType,
  {
    label: string;
    color: string;
    strokeColor: string;
    fillColor: string;
    dataKey: string;
  }
> = {
  spend: {
    label: '消耗',
    color: 'text-blue-600',
    strokeColor: '#2563EB',
    fillColor: '#DBEAFE',
    dataKey: 'spend',
  },
  revenue: {
    label: '收入',
    color: 'text-green-600',
    strokeColor: '#16A34A',
    fillColor: '#DCFCE7',
    dataKey: 'revenue',
  },
  profit: {
    label: '利润',
    color: 'text-amber-600',
    strokeColor: '#D97706',
    fillColor: '#FEF3C7',
    dataKey: 'profit',
  },
  conversions: {
    label: '粉数',
    color: 'text-violet-600',
    strokeColor: '#7C3AED',
    fillColor: '#EDE9FE',
    dataKey: 'conversions',
  },
};

// 格式化 Y 轴数值
const formatYAxis = (value: number, metric: MetricType) => {
  if (metric === 'conversions') {
    return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value.toString();
  }
  return value >= 10000
    ? `¥${(value / 10000).toFixed(1)}w`
    : `¥${(value / 1000).toFixed(1)}k`;
};

// Tooltip Props 类型
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  metric: MetricType;
}

// 格式化 Tooltip
const CustomTooltip = ({ active, payload, label, metric }: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) return null;

  const config = METRIC_CONFIG[metric];
  const value = payload[0].value;

  return (
    <div className="bg-background/95 backdrop-blur-sm border border-border rounded-lg shadow-lg p-3">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={cn('text-sm font-semibold', config.color)}>
        {config.label}:{' '}
        {metric === 'conversions'
          ? value.toLocaleString()
          : `¥${value.toLocaleString()}`}
      </p>
    </div>
  );
};

export function MainTrendChart({
  data,
  activeMetric,
  onMetricChange,
  summary,
  className,
}: MainTrendChartProps) {
  const config = METRIC_CONFIG[activeMetric];

  // 格式化日期显示
  const formattedData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      displayDate: new Date(item.date).toLocaleDateString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
      }),
    }));
  }, [data]);

  // 计算统计数据用于自动总结
  const stats = useMemo(() => {
    if (data.length === 0) return null;

    const values = data
      .map((d) => d[config.dataKey] as number)
      .filter((v) => v !== undefined);
    const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
    const latest = values[values.length - 1];
    const earliest = values[0];
    const change = ((latest - earliest) / earliest) * 100;

    return { avg, latest, change };
  }, [data, config.dataKey]);

  return (
    <Card className={cn('rounded-xl border shadow-sm', className)} id="main-trend-chart">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold text-foreground">
            核心指标趋势
          </CardTitle>
          <div className="flex items-center gap-2">
            {/* 查看明细按钮 */}
            <Link href="/reports">
              <Button variant="outline" size="sm" className="h-8 text-xs">
                <ExternalLink className="h-3.5 w-3.5 mr-1.5" />
                查看明细
              </Button>
            </Link>
          </div>
        </div>

        {/* AI 自动总结区域 */}
        {summary && stats && (
          <div className="mt-4 p-4 bg-muted/50 rounded-lg border border-border/50">
            <div className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">数据洞察：</span>
                {summary}
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {/* 指标切换标签 */}
        <div className="flex gap-2 mb-6">
          {(Object.keys(METRIC_CONFIG) as MetricType[]).map((metric) => {
            const metricConfig = METRIC_CONFIG[metric];
            const isActive = metric === activeMetric;
            return (
              <button
                key={metric}
                onClick={() => onMetricChange?.(metric)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                {metricConfig.label}
              </button>
            );
          })}
        </div>

        {/* 图表区域 */}
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={formattedData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <defs>
              <linearGradient id={`gradient-${activeMetric}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={config.strokeColor} stopOpacity={0.1} />
                <stop offset="95%" stopColor={config.strokeColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} />
            <XAxis
              dataKey="displayDate"
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickLine={false}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickLine={false}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={(value) => formatYAxis(value, activeMetric)}
            />
            <Tooltip
              content={<CustomTooltip metric={activeMetric} />}
              cursor={{ stroke: config.strokeColor, strokeWidth: 1, strokeDasharray: '5 5' }}
            />
            <Line
              type="monotone"
              dataKey={config.dataKey}
              stroke={config.strokeColor}
              strokeWidth={2.5}
              dot={{ fill: config.strokeColor, r: 4 }}
              activeDot={{ r: 6, fill: config.strokeColor }}
              fill={`url(#gradient-${activeMetric})`}
            />
          </LineChart>
        </ResponsiveContainer>

        {/* 底部统计信息 */}
        {stats && (
          <div className="mt-6 pt-4 border-t border-border/50 flex items-center justify-between text-sm">
            <div className="text-muted-foreground">
              期间平均：
              <span className="font-semibold text-foreground ml-1.5">
                {activeMetric === 'conversions'
                  ? stats.avg.toLocaleString(undefined, { maximumFractionDigits: 0 })
                  : `¥${stats.avg.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
              </span>
            </div>
            <div
              className={cn(
                'text-sm font-medium',
                stats.change >= 0 ? 'text-green-600' : 'text-red-600'
              )}
            >
              期间变化：{stats.change >= 0 ? '+' : ''}
              {stats.change.toFixed(1)}%
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * 生成自动总结文案
 * TODO: 未来接入 AI API
 */
export function generateSummary(
  data: TrendDataPoint[],
  metric: MetricType
): string {
  if (data.length === 0) return '';

  const config = METRIC_CONFIG[metric];
  const values = data
    .map((d) => d[config.dataKey] as number)
    .filter((v) => v !== undefined);

  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;
  const latest = values[values.length - 1];
  const earliest = values[0];
  const change = ((latest - earliest) / earliest) * 100;

  const avgStr =
    metric === 'conversions'
      ? avg.toLocaleString(undefined, { maximumFractionDigits: 0 })
      : `¥${avg.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  const changeStr = change >= 0 ? `+${change.toFixed(1)}%` : `${change.toFixed(1)}%`;

  return `近 ${data.length} 天日均${config.label} ${avgStr}，较首日${changeStr}，整体趋势${
    change >= 0 ? '上升' : '下降'
  }。`;
}

export default MainTrendChart;
