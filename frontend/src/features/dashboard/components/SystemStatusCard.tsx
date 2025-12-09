/**
 * SystemStatusCard Component
 *
 * Shows system health status
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Card: shadcn Card, rounded-xl
 * Typography: H3 = text-xl font-semibold
 * Status colors: success (green), warning (yellow), error (red)
 */

'use client';

import React from 'react';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { SystemStatus, SystemStatusItem } from '../types';

interface SystemStatusCardProps {
  status?: SystemStatus;
}

type StatusType = 'healthy' | 'warning' | 'error';

// 对齐 UI_DESIGN_SYSTEM.md 2.3 状态颜色
const STATUS_CONFIG: Record<StatusType, { color: string; icon: typeof CheckCircle; label: string }> = {
  healthy: { color: 'text-green-500', icon: CheckCircle, label: '正常' },
  warning: { color: 'text-yellow-500', icon: AlertTriangle, label: '警告' },
  error: { color: 'text-red-500', icon: XCircle, label: '异常' },
};

export function SystemStatusCard({ status }: SystemStatusCardProps) {
  const defaultStatus: SystemStatus = {
    api: { name: 'API 服务', status: 'healthy' },
    database: { name: '数据库连接', status: 'healthy' },
    scheduler: { name: '定时任务', status: 'healthy' },
  };

  const systemStatus = status || defaultStatus;
  const statusItems: SystemStatusItem[] = [
    systemStatus.api,
    systemStatus.database,
    systemStatus.scheduler,
  ];

  return (
    <Card className="rounded-xl border shadow-sm" data-testid="dashboard-system-status">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-foreground">
          系统状态
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {statusItems.map((item, index) => {
            const config = STATUS_CONFIG[item.status];
            const Icon = config.icon;
            return (
              <div key={index} className="flex items-center gap-3">
                <Icon className={cn('h-4 w-4', config.color)} />
                <span className="text-sm text-foreground">
                  {item.name}
                </span>
                <span className={cn('text-xs ml-auto', config.color)}>
                  {config.label}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default SystemStatusCard;
