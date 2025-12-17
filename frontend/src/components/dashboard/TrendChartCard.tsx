"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp } from 'lucide-react';

interface TrendChartCardProps {
  title: string;
  description?: string;
  trend: {
    value: number;
    isPositive: boolean;
  };
  dataPoints?: Array<{
    label: string;
    value: number;
  }>;
  className?: string;
}

export function TrendChartCard({
  title,
  description,
  trend,
  dataPoints = [],
  className
}: TrendChartCardProps) {
  return (
    <Card className={`rounded-2xl shadow-sm border-slate-200/60 bg-white p-5 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            {description && (
              <p className="text-sm text-slate-500 mt-1">{description}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant={trend.isPositive ? "default" : "destructive"}
              className="text-xs font-medium"
            >
              <TrendingUp className={`w-3 h-3 mr-1 ${!trend.isPositive && 'rotate-180'}`} />
              {trend.value}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {/* 增强的趋势图表：包含示意折线和刻度 */}
        <div className="h-40 bg-slate-50 rounded-lg p-4 relative">
          {/* Y轴刻度 */}
          <div className="absolute left-1 top-2 bottom-8 flex flex-col justify-between text-xs text-slate-400">
            <span>5k</span>
            <span>3k</span>
            <span>1k</span>
          </div>

          {/* 图表区域 */}
          <div className="ml-8 h-full flex items-end justify-between gap-2 relative">
            {/* 网格线 */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
              <div className="border-b border-slate-200/30" />
              <div className="border-b border-slate-200/30" />
              <div className="border-b border-slate-200/30" />
            </div>

            {/* 柱状图 */}
            {dataPoints.map((point, index) => (
              <div key={index} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-sm hover:from-blue-600 hover:to-blue-500 transition-all duration-200 cursor-pointer group relative"
                  style={{ height: `${(point.value / 100) * 100}%` }}
                >
                  <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                    ￥{((point.value / 100) * 5000).toFixed(0)}
                  </div>
                </div>
                <span className="text-xs text-slate-500 mt-1">{point.label.slice(-2)}</span>
              </div>
            ))}

            {/* 示意折线 */}
            <svg className="absolute inset-0 pointer-events-none" style={{ marginLeft: '2rem' }}>
              <polyline
                points={dataPoints.map((point, index) => {
                  const x = (index * 100 / (dataPoints.length - 1)) + '%';
                  const y = 100 - (point.value / 100) * 80 - 10; // 留出上下边距
                  return `${x},${y}%`;
                }).join(' ')}
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2"
                strokeDasharray="4 2"
                opacity="0.6"
              />
            </svg>
          </div>

          {/* X轴标签 */}
          <div className="ml-8 mt-1 flex justify-between px-1 text-xs text-slate-400">
            <span>7天前</span>
            <span>今天</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}