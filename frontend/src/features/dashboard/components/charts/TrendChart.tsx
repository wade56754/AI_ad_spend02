/**
 * TrendChart Component
 *
 * Line chart (curve) for displaying time series data
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Features:
 * - Time range selector (7d/30d/90d)
 * - Smooth curve line with area fill
 * - Hover tooltips with data points
 * - Proper Y-axis scaling and formatting
 */

'use client';

import React, { useState, useMemo, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { TrendDataPoint } from '../../types';

export type TimeRange = '7d' | '30d' | '90d';

export interface TrendChartProps {
  title: string;
  description?: string;
  data: TrendDataPoint[];
  height?: number;
  className?: string;
  testId?: string;
  /** 是否显示时间范围选择器 */
  showTimeRangeSelector?: boolean;
  /** 默认时间范围 */
  defaultTimeRange?: TimeRange;
  /** 时间范围变化回调 */
  onTimeRangeChange?: (range: TimeRange) => void;
  /** 颜色主题 */
  color?: 'blue' | 'green' | 'violet' | 'amber';
  /** 是否显示面积填充 */
  showArea?: boolean;
}

const TIME_RANGE_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '7天' },
  { value: '30d', label: '30天' },
  { value: '90d', label: '90天' },
];

const COLOR_MAP = {
  blue: {
    line: '#3b82f6',
    dot: '#3b82f6',
    areaFrom: 'rgba(59, 130, 246, 0.3)',
    areaTo: 'rgba(59, 130, 246, 0.02)',
    gradient: 'blue'
  },
  green: {
    line: '#22c55e',
    dot: '#22c55e',
    areaFrom: 'rgba(34, 197, 94, 0.3)',
    areaTo: 'rgba(34, 197, 94, 0.02)',
    gradient: 'green'
  },
  violet: {
    line: '#8b5cf6',
    dot: '#8b5cf6',
    areaFrom: 'rgba(139, 92, 246, 0.3)',
    areaTo: 'rgba(139, 92, 246, 0.02)',
    gradient: 'violet'
  },
  amber: {
    line: '#f59e0b',
    dot: '#f59e0b',
    areaFrom: 'rgba(245, 158, 11, 0.3)',
    areaTo: 'rgba(245, 158, 11, 0.02)',
    gradient: 'amber'
  },
};

/**
 * 格式化数值显示
 */
function formatValue(value: number): string {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'k';
  }
  return value.toLocaleString();
}

/**
 * 格式化Y轴刻度
 */
function formatYAxisLabel(value: number): string {
  if (value >= 10000) {
    return (value / 10000).toFixed(0) + '万';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(0) + 'k';
  }
  return value.toString();
}

/**
 * 获取合适的最大值刻度
 */
function getNiceMax(value: number): number {
  if (value === 0) return 100;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const normalized = value / magnitude;
  let nice: number;
  if (normalized <= 1) nice = 1;
  else if (normalized <= 2) nice = 2;
  else if (normalized <= 5) nice = 5;
  else nice = 10;
  return nice * magnitude;
}

/**
 * 生成平滑曲线路径 (Catmull-Rom spline)
 */
function generateSmoothPath(points: { x: number; y: number }[], tension: number = 0.3): string {
  if (points.length < 2) return '';
  if (points.length === 2) {
    return `M ${points[0].x} ${points[0].y} L ${points[1].x} ${points[1].y}`;
  }

  let path = `M ${points[0].x} ${points[0].y}`;

  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(points.length - 1, i + 2)];

    const cp1x = p1.x + (p2.x - p0.x) * tension;
    const cp1y = p1.y + (p2.y - p0.y) * tension;
    const cp2x = p2.x - (p3.x - p1.x) * tension;
    const cp2y = p2.y - (p3.y - p1.y) * tension;

    path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
  }

  return path;
}

/**
 * 趋势图组件 - 曲线图
 * 基于 UI_DESIGN_SYSTEM.md 设计规范
 */
export function TrendChart({
  title,
  description,
  data,
  height = 220,
  className = '',
  testId,
  showTimeRangeSelector = true,
  defaultTimeRange = '7d',
  onTimeRangeChange,
  color = 'blue',
  showArea = true,
}: TrendChartProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>(defaultTimeRange);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const colors = COLOR_MAP[color];

  // 处理时间范围变化
  const handleTimeRangeChange = (range: TimeRange) => {
    setTimeRange(range);
    onTimeRangeChange?.(range);
  };

  // 计算图表数据
  const chartData = useMemo(() => {
    if (data.length === 0) return { data: [], maxValue: 0, minValue: 0, range: 0 };

    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = 0;
    const niceMax = getNiceMax(maxValue);

    return {
      data,
      maxValue: niceMax,
      minValue,
      range: niceMax - minValue,
    };
  }, [data]);

  // 获取Y轴刻度
  const yAxisTicks = useMemo(() => {
    const ticks = 5;
    const step = chartData.maxValue / (ticks - 1);
    return Array.from({ length: ticks }, (_, i) => {
      const value = chartData.maxValue - step * i;
      return {
        value,
        label: formatYAxisLabel(Math.round(value)),
      };
    });
  }, [chartData.maxValue]);

  // 格式化日期标签
  const formatLabel = (date: string, dataLength: number) => {
    const d = new Date(date);
    if (dataLength > 15) {
      return d.getDate().toString();
    }
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  // 决定显示哪些X轴标签
  const visibleLabelIndices = useMemo(() => {
    const len = data.length;
    if (len <= 7) return data.map((_, i) => i);
    if (len <= 15) return data.map((_, i) => i).filter(i => i % 2 === 0 || i === len - 1);
    if (len <= 31) return data.map((_, i) => i).filter(i => i % 5 === 0 || i === len - 1);
    return data.map((_, i) => i).filter(i => i % 10 === 0 || i === len - 1);
  }, [data]);

  const chartHeight = height - 48;
  const svgPadding = { top: 10, right: 10, bottom: 0, left: 0 };

  // 计算点的位置
  const points = useMemo(() => {
    if (data.length === 0 || chartData.range === 0) return [];

    return data.map((point, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - ((point.value - chartData.minValue) / chartData.range) * 100;
      return { x, y, value: point.value, date: point.date };
    });
  }, [data, chartData]);

  // 生成曲线路径
  const linePath = useMemo(() => {
    if (points.length < 2) return '';
    return generateSmoothPath(points.map(p => ({ x: p.x, y: p.y })));
  }, [points]);

  // 生成面积路径
  const areaPath = useMemo(() => {
    if (points.length < 2) return '';
    const path = generateSmoothPath(points.map(p => ({ x: p.x, y: p.y })));
    return `${path} L ${points[points.length - 1].x} 100 L ${points[0].x} 100 Z`;
  }, [points]);

  // 处理鼠标移动
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!chartRef.current || points.length === 0) return;

    const rect = chartRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;

    // 找到最近的数据点
    let closestIndex = 0;
    let closestDistance = Infinity;

    points.forEach((point, index) => {
      const distance = Math.abs(point.x - x);
      if (distance < closestDistance) {
        closestDistance = distance;
        closestIndex = index;
      }
    });

    setHoveredIndex(closestIndex);
  };

  const handleMouseLeave = () => {
    setHoveredIndex(null);
  };

  const gradientId = `gradient-${color}-${testId || 'default'}`;

  return (
    <Card className={cn('rounded-xl border shadow-sm', className)} data-testid={testId}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-semibold text-foreground">
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-sm text-muted-foreground mt-1">
                {description}
              </CardDescription>
            )}
          </div>

          {/* 时间范围选择器 */}
          {showTimeRangeSelector && (
            <div className="flex gap-1 bg-muted rounded-lg p-1">
              {TIME_RANGE_OPTIONS.map(option => (
                <Button
                  key={option.value}
                  variant={timeRange === option.value ? 'secondary' : 'ghost'}
                  size="sm"
                  className={cn(
                    'h-7 px-3 text-xs font-medium transition-all',
                    timeRange === option.value
                      ? 'bg-background shadow-sm text-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                  onClick={() => handleTimeRangeChange(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-4 pt-2">
        {data.length === 0 ? (
          <div
            className="flex items-center justify-center text-muted-foreground text-sm"
            style={{ height: `${chartHeight}px` }}
          >
            暂无数据
          </div>
        ) : (
          <div style={{ height: `${chartHeight}px` }} className="relative">
            {/* Y轴刻度 */}
            <div
              className="absolute left-0 top-0 w-12 flex flex-col justify-between text-xs text-muted-foreground pr-2"
              style={{ height: `${chartHeight - 24}px` }}
            >
              {yAxisTicks.map((tick, index) => (
                <div key={index} className="text-right leading-none">
                  {tick.label}
                </div>
              ))}
            </div>

            {/* 图表区域 */}
            <div
              ref={chartRef}
              className="ml-14 relative cursor-crosshair"
              style={{ height: `${chartHeight - 24}px` }}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              {/* 网格线 */}
              <div className="absolute inset-0 pointer-events-none">
                {yAxisTicks.map((_, index) => (
                  <div
                    key={index}
                    className="absolute w-full border-b border-border/30"
                    style={{ top: `${(index / (yAxisTicks.length - 1)) * 100}%` }}
                  />
                ))}
              </div>

              {/* SVG 曲线图 */}
              <svg
                className="absolute inset-0 overflow-visible"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                style={{ width: '100%', height: '100%' }}
              >
                <defs>
                  <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={colors.areaFrom} />
                    <stop offset="100%" stopColor={colors.areaTo} />
                  </linearGradient>
                </defs>

                {/* 面积填充 */}
                {showArea && areaPath && (
                  <path
                    d={areaPath}
                    fill={`url(#${gradientId})`}
                    className="transition-all duration-300"
                  />
                )}

                {/* 曲线 */}
                {linePath && (
                  <path
                    d={linePath}
                    fill="none"
                    stroke={colors.line}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    vectorEffect="non-scaling-stroke"
                    className="transition-all duration-300"
                  />
                )}
              </svg>

              {/* 数据点 */}
              {points.map((point, index) => {
                const isHovered = hoveredIndex === index;
                const showDot = data.length <= 31 || isHovered;

                return (
                  <div
                    key={index}
                    className="absolute transform -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                    style={{
                      left: `${point.x}%`,
                      top: `${point.y}%`,
                    }}
                  >
                    {showDot && (
                      <div
                        className={cn(
                          'rounded-full transition-all duration-150',
                          isHovered ? 'ring-4 ring-opacity-30' : ''
                        )}
                        style={{
                          width: isHovered ? '10px' : '6px',
                          height: isHovered ? '10px' : '6px',
                          backgroundColor: colors.dot,
                          boxShadow: `0 0 0 2px white, 0 0 0 3px ${colors.dot}`,
                        }}
                      />
                    )}
                  </div>
                );
              })}

              {/* 悬停提示 */}
              {hoveredIndex !== null && points[hoveredIndex] && (
                <>
                  {/* 垂直参考线 */}
                  <div
                    className="absolute top-0 bottom-0 w-px bg-border/50 pointer-events-none"
                    style={{ left: `${points[hoveredIndex].x}%` }}
                  />

                  {/* 提示框 */}
                  <div
                    className={cn(
                      'absolute z-20 pointer-events-none',
                      'bg-popover text-popover-foreground text-xs px-3 py-2 rounded-lg',
                      'shadow-lg border transform -translate-x-1/2'
                    )}
                    style={{
                      left: `${points[hoveredIndex].x}%`,
                      top: `${Math.max(10, points[hoveredIndex].y - 15)}%`,
                      transform: `translate(-50%, -100%)`,
                    }}
                  >
                    <div className="font-semibold text-sm">{formatValue(points[hoveredIndex].value)}</div>
                    <div className="text-muted-foreground">{formatLabel(points[hoveredIndex].date, 1)}</div>
                  </div>
                </>
              )}
            </div>

            {/* X轴标签 */}
            <div className="ml-14 flex text-xs text-muted-foreground mt-2">
              {data.map((point, index) => (
                <div
                  key={index}
                  className="flex-1 text-center"
                  style={{ minWidth: 0 }}
                >
                  {visibleLabelIndices.includes(index) ? formatLabel(point.date, data.length) : ''}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TrendChart;
