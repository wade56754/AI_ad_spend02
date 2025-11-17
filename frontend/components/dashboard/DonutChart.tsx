'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// 类型定义
export interface ChartData {
  name: string;
  value: number;
  color: string;
}

export interface DonutChartProps {
  title: string;
  data: ChartData[];
  size?: number;
  className?: string;
  centerContent?: React.ReactNode;
}

/**
 * 环形图组件
 * 基于Figma设计的环形图样式
 */
export const DonutChart: React.FC<DonutChartProps> = ({
  title,
  data,
  size = 200,
  className = '',
  centerContent
}) => {
  // 计算总和
  const total = data.reduce((sum, item) => sum + item.value, 0);

  // 计算每个扇形的角度
  const calculateAngles = () => {
    let currentAngle = -90; // 从顶部开始
    return data.map(item => {
      const percentage = (item.value / total) * 100;
      const angle = (item.value / total) * 360;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      currentAngle = endAngle;

      return {
        ...item,
        percentage,
        startAngle,
        endAngle,
        angle
      };
    });
  };

  // 创建SVG路径
  const createPath = (startAngle: number, endAngle: number, innerRadius: number, outerRadius: number) => {
    const startAngleRad = (startAngle * Math.PI) / 180;
    const endAngleRad = (endAngle * Math.PI) / 180;

    const x1 = Math.cos(startAngleRad) * outerRadius + size / 2;
    const y1 = Math.sin(startAngleRad) * outerRadius + size / 2;
    const x2 = Math.cos(endAngleRad) * outerRadius + size / 2;
    const y2 = Math.sin(endAngleRad) * outerRadius + size / 2;

    const x3 = Math.cos(endAngleRad) * innerRadius + size / 2;
    const y3 = Math.sin(endAngleRad) * innerRadius + size / 2;
    const x4 = Math.cos(startAngleRad) * innerRadius + size / 2;
    const y4 = Math.sin(startAngleRad) * innerRadius + size / 2;

    const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;

    return [
      `M ${x1} ${y1}`,
      `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      `L ${x3} ${y3}`,
      `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x4} ${y4}`,
      'Z'
    ].join(' ');
  };

  const chartData = calculateAngles();
  const innerRadius = size * 0.6;
  const outerRadius = size * 0.45;

  return (
    <Card className={`bg-white rounded-xl border border-gray-200 ${className}`}>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-semibold text-gray-900">
          {title}
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-2">
        <div className="flex flex-col items-center">
          {/* SVG环形图 */}
          <div className="relative">
            <svg width={size} height={size} className="transform -rotate-90">
              {chartData.map((segment, index) => (
                <path
                  key={index}
                  d={createPath(segment.startAngle, segment.endAngle, innerRadius, outerRadius)}
                  fill={segment.color}
                  stroke="white"
                  strokeWidth="2"
                  className="transition-all duration-200 hover:opacity-80 cursor-pointer"
                />
              ))}
            </svg>

            {/* 中心内容 */}
            {centerContent && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="transform rotate-90 text-center">
                  {centerContent}
                </div>
              </div>
            )}
          </div>

          {/* 图例 */}
          <div className="mt-6 space-y-2 w-full">
            {chartData.map((segment, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: segment.color }}
                  />
                  <span className="text-gray-600">{segment.name}</span>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">{segment.value.toLocaleString()}</div>
                  <div className="text-xs text-gray-500">{segment.percentage.toFixed(1)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DonutChart;