/**
 * AlertBanner Component
 *
 * 今日风险/待办提示条 - 显示紧急告警、需关注项和待办事项
 * 点击可跳转或滚动到对应模块
 *
 * Based on UI_DESIGN_SYSTEM.md v2.0 - 状态颜色规范
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, AlertCircle, CheckCircle2, ChevronRight, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type AlertSeverity = 'critical' | 'warning' | 'info';

export interface Alert {
  id: string;
  severity: AlertSeverity;
  message: string;
  href?: string; // 跳转链接
  scrollTo?: string; // 页面内滚动目标
  count?: number; // 数量（用于待办）
}

interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (alertId: string) => void;
  className?: string;
}

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  {
    icon: React.ComponentType<{ className?: string }>;
    bgClass: string;
    textClass: string;
    iconClass: string;
    emoji: string;
  }
> = {
  critical: {
    icon: AlertTriangle,
    bgClass: 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900',
    textClass: 'text-red-900 dark:text-red-200',
    iconClass: 'text-red-600 dark:text-red-400',
    emoji: '🔴',
  },
  warning: {
    icon: AlertCircle,
    bgClass: 'bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-900',
    textClass: 'text-orange-900 dark:text-orange-200',
    iconClass: 'text-orange-600 dark:text-orange-400',
    emoji: '🟠',
  },
  info: {
    icon: CheckCircle2,
    bgClass: 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900',
    textClass: 'text-blue-900 dark:text-blue-200',
    iconClass: 'text-blue-600 dark:text-blue-400',
    emoji: '🟡',
  },
};

function AlertItem({
  alert,
  onDismiss,
}: {
  alert: Alert;
  onDismiss?: (id: string) => void;
}) {
  const config = SEVERITY_CONFIG[alert.severity];
  const Icon = config.icon;

  const handleClick = () => {
    if (alert.scrollTo) {
      const element = document.getElementById(alert.scrollTo);
      element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const content = (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-lg border transition-colors',
        config.bgClass,
        (alert.href || alert.scrollTo) && 'cursor-pointer hover:shadow-sm'
      )}
      onClick={alert.scrollTo ? handleClick : undefined}
    >
      <Icon className={cn('h-4 w-4 flex-shrink-0', config.iconClass)} />
      <div className="flex-1 min-w-0">
        <p className={cn('text-sm font-medium', config.textClass)}>
          <span className="mr-1.5">{config.emoji}</span>
          <span className="font-semibold">
            {alert.severity === 'critical'
              ? '紧急'
              : alert.severity === 'warning'
              ? '需关注'
              : '待办'}
            ：
          </span>
          {alert.message}
          {alert.count !== undefined && (
            <span className="ml-1.5 font-bold">{alert.count}</span>
          )}
        </p>
      </div>
      {(alert.href || alert.scrollTo) && (
        <ChevronRight className={cn('h-4 w-4 flex-shrink-0', config.iconClass)} />
      )}
      {onDismiss && (
        <Button
          variant="ghost"
          size="sm"
          className={cn('h-6 w-6 p-0 hover:bg-transparent', config.textClass)}
          onClick={(e) => {
            e.stopPropagation();
            onDismiss(alert.id);
          }}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );

  if (alert.href && !alert.scrollTo) {
    return <Link href={alert.href}>{content}</Link>;
  }

  return content;
}

export function AlertBanner({ alerts, onDismiss, className }: AlertBannerProps) {
  if (alerts.length === 0) {
    return null;
  }

  return (
    <Card className={cn('border-0 shadow-none bg-transparent p-0', className)}>
      <div className="space-y-2">
        {alerts.map((alert) => (
          <AlertItem key={alert.id} alert={alert} onDismiss={onDismiss} />
        ))}
      </div>
    </Card>
  );
}

/**
 * 生成模拟告警数据的辅助函数
 * TODO: 替换为实际 API 数据
 */
export function generateMockAlerts(): Alert[] {
  const alerts: Alert[] = [];

  // 示例：余额不足告警
  const hasBalanceAlert = Math.random() > 0.7;
  if (hasBalanceAlert) {
    alerts.push({
      id: 'balance-warning',
      severity: 'critical',
      message: '账户 X 预计 2 天后余额不足',
      href: '/suppliers',
    });
  }

  // 示例：消耗异常告警
  const hasSpendAlert = Math.random() > 0.5;
  if (hasSpendAlert) {
    alerts.push({
      id: 'spend-spike',
      severity: 'warning',
      message: '今日消耗较 7 日均值 +65%',
      scrollTo: 'main-trend-chart',
    });
  }

  // 示例：待办事项提醒
  const pendingCount = Math.floor(Math.random() * 10) + 1;
  alerts.push({
    id: 'pending-tasks',
    severity: 'info',
    message: `条待处理事项`,
    count: pendingCount,
    scrollTo: 'pending-tasks-section',
  });

  return alerts;
}

export default AlertBanner;
