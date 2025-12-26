/**
 * StatCard Component (Enhanced)
 *
 * SoT: docs/10.module-specs/A1-dashboard.md §3.2 组件清单
 *
 * 增强版 KPI 卡片:
 * - 主数值: 大字显示
 * - 副信息1: 较昨日变化百分比 (明确说明对比维度)
 * - 副信息2: 7日均值
 * - 目标/预算: 显示 CPL 目标或预算范围
 * - 交互: 点击可切换主图指标
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export type StatCardColor = 'blue' | 'green' | 'purple' | 'orange' | 'red';

export interface StatCardProps {
  title: string;
  value: string | number;
  change?: number | null; // 较昨日变化百分比
  average7d?: string | number; // 7日均值
  target?: string; // 目标/预算说明，如 "目标 ROAS ≥ 1.8" 或 "预算 ¥100k-130k"
  icon: React.ReactNode;
  color: StatCardColor;
  onClick?: () => void; // 点击回调
  href?: string; // 点击导航链接
  isActive?: boolean; // 是否为选中状态 (用于主图联动)
  isWarning?: boolean; // Phase 1: 是否显示警告样式 (不阻断操作)
  testId?: string;
}

// 对齐 UI_DESIGN_SYSTEM.md 2.4 图表颜色
const colorClasses: Record<
  StatCardColor,
  {
    bg: string;
    text: string;
    activeBorder: string;
    activeRing: string;
  }
> = {
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-950/30',
    text: 'text-blue-600 dark:text-blue-400',
    activeBorder: 'border-blue-500',
    activeRing: 'ring-2 ring-blue-500/20',
  },
  green: {
    bg: 'bg-green-100 dark:bg-green-950/30',
    text: 'text-green-600 dark:text-green-400',
    activeBorder: 'border-green-500',
    activeRing: 'ring-2 ring-green-500/20',
  },
  purple: {
    bg: 'bg-violet-100 dark:bg-violet-950/30',
    text: 'text-violet-600 dark:text-violet-400',
    activeBorder: 'border-violet-500',
    activeRing: 'ring-2 ring-violet-500/20',
  },
  orange: {
    bg: 'bg-amber-100 dark:bg-amber-950/30',
    text: 'text-amber-600 dark:text-amber-400',
    activeBorder: 'border-amber-500',
    activeRing: 'ring-2 ring-amber-500/20',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-950/30',
    text: 'text-red-600 dark:text-red-400',
    activeBorder: 'border-red-500',
    activeRing: 'ring-2 ring-red-500/20',
  },
};

export function StatCard({
  title,
  value,
  change,
  average7d,
  target,
  icon,
  color,
  onClick,
  href,
  isActive = false,
  isWarning = false,
  testId,
}: StatCardProps) {
  const colorStyle = colorClasses[color];

  // Phase 1: 警告样式类 (高亮但不阻断)
  const warningClasses = isWarning
    ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800'
    : '';

  const cardContent = (
    <Card
      className={cn(
        'rounded-xl border shadow-sm transition-all duration-200',
        (onClick || href) && 'cursor-pointer hover:shadow-lg hover:-translate-y-0.5',
        isActive && [colorStyle.activeBorder, colorStyle.activeRing, 'shadow-md'],
        warningClasses
      )}
      onClick={href ? undefined : onClick}
      data-testid={testId}
    >
      <CardContent className="p-6">
        {/* 顶部: 图标 + 变化指示器 */}
        <div className="flex items-center justify-between mb-4">
          <div className={cn('p-3 rounded-lg', colorStyle.bg, colorStyle.text)}>
            {icon}
          </div>
          {change !== null && change !== undefined && (
            <div
              className={cn(
                'flex items-center text-sm font-medium px-2.5 py-1 rounded-full',
                change >= 0
                  ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30'
                  : 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/30'
              )}
            >
              {change >= 0 ? (
                <TrendingUp className="h-3.5 w-3.5 mr-1" />
              ) : (
                <TrendingDown className="h-3.5 w-3.5 mr-1" />
              )}
              {Math.abs(change).toFixed(1)}%
            </div>
          )}
        </div>

        {/* 主数值 */}
        <div className="text-3xl font-bold text-foreground mb-1 tracking-tight">
          {value}
        </div>

        {/* 标题 */}
        <div className="text-sm font-medium text-muted-foreground mb-3">{title}</div>

        {/* 底部信息条 */}
        <div className="space-y-2 pt-3 border-t border-border/50">
          <div className="flex items-center justify-between">
            {/* 较昨日变化 */}
            {change !== null && change !== undefined && (
              <div className="text-xs text-muted-foreground">
                较昨日{' '}
                <span
                  className={cn(
                    'font-semibold',
                    change >= 0 ? 'text-green-600' : 'text-red-600'
                  )}
                >
                  {change >= 0 ? '+' : ''}
                  {change.toFixed(1)}%
                </span>
              </div>
            )}

            {/* 7日均值 */}
            {average7d !== undefined && (
              <div className="text-xs text-muted-foreground text-right">
                7日均值{' '}
                <span className="font-medium text-foreground">{average7d}</span>
              </div>
            )}
          </div>

          {/* 目标/预算 */}
          {target && (
            <div className="text-xs text-muted-foreground bg-muted/30 px-2 py-1 rounded">
              {target}
            </div>
          )}
        </div>

        {/* 选中状态提示 */}
        {isActive && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <div className={cn('text-xs font-medium', colorStyle.text)}>
              ● 查看趋势图
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  // 如果有 href，包装在 Link 中
  if (href) {
    return <Link href={href}>{cardContent}</Link>;
  }

  return cardContent;
}

export default StatCard;
