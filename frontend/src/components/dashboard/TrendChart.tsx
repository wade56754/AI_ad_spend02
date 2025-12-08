'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// 类型定义
export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendChartProps {
  title: string;
  description?: string;
  data: TrendDataPoint[];
  height?: number;
  className?: string;
  showTrend?: boolean;
}

/**
 * 趋势图组件
 * 基于Figma设计的柱状图样式
 */
export const TrendChart: React.FC<TrendChartProps> = ({
  title,
  description,
  data,
  height = 200,
  className = '',
  showTrend = true
}) => {
  // 计算最大值用于缩放
  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = 0;
  const range = maxValue - minValue;

  // 获取Y轴刻度
  const getYAxisTicks = () => {
    const ticks = 5;
    const step = range / (ticks - 1);
    return Array.from({ length: ticks }, (_, i) => ({
      value: Math.round((maxValue - step * i) / 100) * 100,
      label: Math.round((maxValue - step * i) / 100).toString()
    }));
  };

  // 格式化日期标签
  const formatLabel = (date: string) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  // 获取柱状图颜色
  const getBarColor = (value: number, index: number) => {
    // 简单的渐变效果
    if (index === data.length - 1) return 'bg-blue-500'; // 最新数据高亮
    return 'bg-blue-400';
  };

  return (
    <Card className={`bg-white rounded-xl border border-gray-200 ${className}`}>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold text-gray-900">
          {title}
        </CardTitle>
        {description && (
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        )}
      </CardHeader>

      <CardContent className="p-0 pt-2">
        <div style={{ height: `${height}px` }} className="relative">
          {/* Y轴刻度 */}
          <div className="absolute left-0 top-0 bottom-8 w-12 flex flex-col justify-between text-xs text-gray-400">
            {getYAxisTicks().map((tick, index) => (
              <div key={index} className="text-right pr-2">
                {tick.label}
              </div>
            ))}
          </div>

          {/* 图表区域 */}
          <div
            className="ml-14 h-full flex items-end justify-between relative"
            style={{ paddingBottom: '32px' }}
          >
            {/* 网格线 */}
            <div className="absolute inset-0 pointer-events-none">
              {getYAxisTicks().slice(0, -1).map((_, index) => (
                <div
                  key={index}
                  className="absolute w-full border-b border-gray-100"
                  style={{ bottom: `${(index + 1) * (100 / (getYAxisTicks().length - 1))}%` }}
                />
              ))}
            </div>

            {/* 柱状图 */}
            {data.map((point, index) => {
              const height = range > 0 ? ((point.value - minValue) / range) * 100 : 0;
              const isLast = index === data.length - 1;

              return (
                <div
                  key={index}
                  className="flex-1 flex flex-col items-center group relative"
                  style={{ maxWidth: '40px', margin: '0 2px' }}
                >
                  <div
                    className={`w-full rounded-t transition-all duration-200 cursor-pointer ${
                      isLast ? 'bg-blue-500' : 'bg-blue-400'
                    } hover:bg-blue-600 relative`}
                    style={{ height: `${height}%` }}
                  >
                    {/* 悬停提示 */}
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                      {point.value.toLocaleString()}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* 趋势线（可选） */}
            {showTrend && data.length > 1 && (
              <svg
                className="absolute inset-0 pointer-events-none"
                style={{ marginLeft: '14px', marginBottom: '32px' }}
              >
                <polyline
                  points={data.map((point, index) => {
                    const x = (index / (data.length - 1)) * 100;
                    const y = 100 - ((point.value - minValue) / range) * 100;
                    return `${x}%,${y}%`;
                  }).join(' ')}
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="2"
                  strokeDasharray="4 2"
                  opacity="0.4"
                />

                {/* 数据点 */}
                {data.map((point, index) => {
                  const x = (index / (data.length - 1)) * 100;
                  const y = 100 - ((point.value - minValue) / range) * 100;
                  return (
                    <circle
                      key={index}
                      cx={`${x}%`}
                      cy={`${y}%`}
                      r="3"
                      fill="#3b82f6"
                      opacity="0.6"
                    />
                  );
                })}
              </svg>
            )}
          </div>

          {/* X轴标签 */}
          <div className="absolute left-14 right-0 bottom-0 flex justify-between text-xs text-gray-400">
            {data.map((point, index) => (
              <div
                key={index}
                className="text-center"
                style={{ minWidth: '30px', margin: '0 2px' }}
              >
                {formatLabel(point.date)}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TrendChart;