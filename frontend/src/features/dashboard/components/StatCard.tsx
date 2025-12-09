/**
 * StatCard Component
 *
 * Individual stat card with value, change indicator and icon
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Card: rounded-xl, border, shadow-sm, p-6
 * Typography: value = text-2xl font-bold, title = text-sm
 * Colors: 图表颜色规范
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export type StatCardColor = 'blue' | 'green' | 'purple' | 'orange' | 'red';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null;
  icon: React.ReactNode;
  color: StatCardColor;
  href?: string;
  testId?: string;
}

// 对齐 UI_DESIGN_SYSTEM.md 2.4 图表颜色
const colorClasses: Record<StatCardColor, { bg: string; text: string }> = {
  blue: { bg: 'bg-blue-100', text: 'text-blue-500' },    // 消耗/支出
  green: { bg: 'bg-green-100', text: 'text-green-500' }, // 收入
  purple: { bg: 'bg-violet-100', text: 'text-violet-500' }, // 粉数
  orange: { bg: 'bg-amber-100', text: 'text-amber-500' },   // 利润
  red: { bg: 'bg-red-100', text: 'text-red-500' },
};

export function StatCard({
  title,
  value,
  change,
  icon,
  color,
  href,
  testId,
}: StatCardProps) {
  const colorStyle = colorClasses[color];

  const content = (
    <Card
      className={cn(
        'rounded-xl border shadow-sm transition-shadow hover:shadow-md',
        href && 'cursor-pointer'
      )}
      data-testid={testId}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={cn('p-3 rounded-lg', colorStyle.bg, colorStyle.text)}>
            {icon}
          </div>
          {change !== null && change !== undefined && (
            <div
              className={cn(
                'flex items-center text-sm font-medium',
                change >= 0 ? 'text-green-600' : 'text-red-600'
              )}
            >
              {change >= 0 ? (
                <TrendingUp className="h-4 w-4 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 mr-1" />
              )}
              {Math.abs(change).toFixed(1)}%
            </div>
          )}
        </div>
        <div className="text-2xl font-bold text-foreground mb-1">{value}</div>
        <div className="text-sm text-muted-foreground">{title}</div>
      </CardContent>
    </Card>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }

  return content;
}

export default StatCard;
