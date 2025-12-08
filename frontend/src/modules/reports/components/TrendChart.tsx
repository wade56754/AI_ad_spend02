/**
 * TrendChart Component
 *
 * Simple line chart for displaying trend data
 * Uses CSS-based visualization (no chart library dependency)
 */

'use client';

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import type { TrendDataPoint } from '../types';

interface TrendChartProps {
  data: TrendDataPoint[];
  title: string;
  color?: 'blue' | 'green' | 'purple';
  formatValue?: (value: number) => string;
  loading?: boolean;
}

export function TrendChart({
  data,
  title,
  color = 'blue',
  formatValue = (v) => v.toLocaleString(),
  loading = false,
}: TrendChartProps) {
  const colorStyles = {
    blue: {
      gradient: 'from-blue-500 to-blue-600',
      line: 'bg-blue-500',
      dot: 'bg-blue-600',
      text: 'text-blue-600',
      light: 'bg-blue-50',
    },
    green: {
      gradient: 'from-green-500 to-green-600',
      line: 'bg-green-500',
      dot: 'bg-green-600',
      text: 'text-green-600',
      light: 'bg-green-50',
    },
    purple: {
      gradient: 'from-purple-500 to-purple-600',
      line: 'bg-purple-500',
      dot: 'bg-purple-600',
      text: 'text-purple-600',
      light: 'bg-purple-50',
    },
  };

  const styles = colorStyles[color];

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-32 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-sm font-medium text-gray-500 mb-4">{title}</h3>
        <div className="h-32 flex items-center justify-center text-gray-400">
          暂无数据
        </div>
      </div>
    );
  }

  // Calculate chart dimensions
  const values = data.map((d) => d.value);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const range = maxValue - minValue || 1;

  // Calculate trend
  const firstValue = values[0];
  const lastValue = values[values.length - 1];
  const trend = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <div
          className={`flex items-center text-sm ${
            trend >= 0 ? 'text-green-600' : 'text-red-600'
          }`}
        >
          {trend >= 0 ? (
            <TrendingUp className="h-4 w-4 mr-1" />
          ) : (
            <TrendingDown className="h-4 w-4 mr-1" />
          )}
          <span>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}%</span>
        </div>
      </div>

      {/* Chart Container */}
      <div className="relative h-32">
        {/* Grid Lines */}
        <div className="absolute inset-0 flex flex-col justify-between">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="border-b border-gray-100" />
          ))}
        </div>

        {/* Bars */}
        <div className="absolute inset-0 flex items-end justify-between gap-1 pt-4">
          {data.map((point, index) => {
            const height = ((point.value - minValue) / range) * 100;
            const heightPercent = Math.max(height, 5); // Minimum 5% height for visibility

            return (
              <div
                key={index}
                className="flex-1 flex flex-col items-center group relative"
              >
                {/* Bar */}
                <div
                  className={`w-full rounded-t ${styles.light} transition-all duration-200 group-hover:opacity-80`}
                  style={{ height: `${heightPercent}%` }}
                >
                  <div
                    className={`w-full h-full rounded-t bg-gradient-to-t ${styles.gradient} opacity-80`}
                  />
                </div>

                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
                  <div className="bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
                    <div className="font-medium">{formatDate(point.date)}</div>
                    <div>{formatValue(point.value)}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* X-axis Labels */}
      <div className="flex justify-between mt-2 text-xs text-gray-400">
        {data.length > 0 && (
          <>
            <span>{formatDate(data[0].date)}</span>
            {data.length > 4 && (
              <span>{formatDate(data[Math.floor(data.length / 2)].date)}</span>
            )}
            <span>{formatDate(data[data.length - 1].date)}</span>
          </>
        )}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-xs text-gray-400">最高</div>
          <div className={`text-sm font-medium ${styles.text}`}>
            {formatValue(maxValue)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-400">平均</div>
          <div className="text-sm font-medium text-gray-700">
            {formatValue(values.reduce((a, b) => a + b, 0) / values.length)}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-400">最低</div>
          <div className="text-sm font-medium text-gray-500">
            {formatValue(minValue)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TrendChart;
