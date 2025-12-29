/**
 * StatusCard Component
 *
 * SoT: docs/3.dev-guides/DASHBOARD_LAYOUT_SPEC.md §3.2
 *
 * 运营状态卡片 - 用于显示活跃项目数、异常项目数、待审批充值等
 * 特点:
 * - 状态边框颜色 (normal/warning/critical)
 * - 大号数字显示
 * - 可选描述文字
 * - 可选操作按钮
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type StatusType = 'normal' | 'warning' | 'critical';

export interface StatusCardProps {
  title: string;
  count: number;
  status: StatusType;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  href?: string;
  icon?: React.ReactNode;
  testId?: string;
}

const statusStyles: Record<StatusType, {
  border: string;
  bg: string;
  text: string;
  iconBg: string;
}> = {
  normal: {
    border: 'border-l-4 border-l-green-500',
    bg: 'bg-green-50/50 dark:bg-green-950/20',
    text: 'text-green-600 dark:text-green-400',
    iconBg: 'bg-green-100 dark:bg-green-900/30',
  },
  warning: {
    border: 'border-l-4 border-l-orange-500',
    bg: 'bg-orange-50/50 dark:bg-orange-950/20',
    text: 'text-orange-600 dark:text-orange-400',
    iconBg: 'bg-orange-100 dark:bg-orange-900/30',
  },
  critical: {
    border: 'border-l-4 border-l-red-500',
    bg: 'bg-red-50/50 dark:bg-red-950/20',
    text: 'text-red-600 dark:text-red-400',
    iconBg: 'bg-red-100 dark:bg-red-900/30',
  },
};

export function StatusCard({
  title,
  count,
  status,
  description,
  actionLabel,
  onAction,
  href,
  icon,
  testId,
}: StatusCardProps) {
  const style = statusStyles[status];

  const cardContent = (
    <Card
      className={cn(
        'rounded-xl shadow-sm transition-all duration-200',
        style.border,
        href && 'cursor-pointer hover:shadow-md hover:-translate-y-0.5'
      )}
      data-testid={testId}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          {/* 左侧: 图标 + 内容 */}
          <div className="flex-1">
            {/* 图标 */}
            {icon && (
              <div className={cn('inline-flex p-2.5 rounded-lg mb-3', style.iconBg, style.text)}>
                {icon}
              </div>
            )}

            {/* 标题 */}
            <div className="text-sm font-medium text-muted-foreground mb-1">
              {title}
            </div>

            {/* 主数值 */}
            <div className={cn('text-4xl font-bold tracking-tight', style.text)}>
              {count.toLocaleString()}
            </div>

            {/* 描述 */}
            {description && (
              <div className="text-xs text-muted-foreground mt-2">
                {description}
              </div>
            )}
          </div>
        </div>

        {/* 操作按钮 */}
        {(actionLabel || href) && (
          <div className="mt-4 pt-3 border-t border-border/50">
            {href ? (
              <span className={cn('text-sm font-medium', style.text)}>
                {actionLabel || '查看详情'} &rarr;
              </span>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                className={cn('p-0 h-auto', style.text)}
                onClick={onAction}
              >
                {actionLabel}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (href) {
    return <Link href={href}>{cardContent}</Link>;
  }

  return cardContent;
}

export default StatusCard;
