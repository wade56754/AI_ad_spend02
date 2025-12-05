/**
 * Dashboard 风险预警面板组件
 * 
 * 功能：
 * - 列表化展示风险预警
 * - 优先级标签醒目显示
 * - 紧凑布局，增强危险感
 * - 支持点击跳转详情
 */

'use client';

import React from 'react';
import { AlertTriangle, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { RiskAlert } from '../types';

interface DashboardRiskPanelProps {
  alerts: RiskAlert[];
  className?: string;
  onViewAll?: () => void;
  onAlertClick?: (alert: RiskAlert) => void;
}

export function DashboardRiskPanel({
  alerts,
  className,
  onViewAll,
  onAlertClick
}: DashboardRiskPanelProps) {
  const criticalCount = alerts.filter(a => a.level === 'critical').length;

  return (
    <Card className={cn('rounded-lg border-border-default bg-card-bg', className)}>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-center">
          <CardTitle className="text-base flex items-center gap-2 text-text-strong">
            <AlertTriangle className="w-4 h-4 text-warning" />
            风险预警
          </CardTitle>
          {criticalCount > 0 && (
            <Badge
              variant="destructive"
              className="text-xs font-semibold animate-pulse bg-danger/10 text-danger border-danger/20"
            >
              {alerts.length} 待处理
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-text-subtle text-sm">
            暂无风险预警
          </div>
        ) : (
          <>
            {alerts.map((alert) => (
              <div
                key={alert.id}
                onClick={() => onAlertClick?.(alert)}
                className={cn(
                  'p-2.5 bg-shell border rounded-lg transition-all',
                  'hover:bg-elevated hover:border-border-muted',
                  'cursor-pointer group',
                  alert.level === 'critical'
                    ? 'border-border-danger hover:border-danger/50'
                    : 'border-border-default'
                )}
              >
                <div className="flex justify-between items-start mb-1.5">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-text-body group-hover:text-accent transition-colors truncate">
                        {alert.account}
                      </span>
                      {alert.project && (
                        <span className="text-xs text-text-subtle truncate">
                          · {alert.project}
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-medium text-text-muted mb-1">
                      {alert.type}
                    </div>
                  </div>
                  <Badge
                    variant={alert.level === 'critical' ? 'destructive' : 'secondary'}
                    className={cn(
                      'text-[10px] px-2 py-0.5 uppercase tracking-wide font-bold border shrink-0 ml-2',
                      alert.level === 'critical'
                        ? 'bg-danger/20 text-danger-light border-danger/40'
                        : 'bg-warning/20 text-warning-light border-warning/40'
                    )}
                  >
                    {alert.level === 'critical' ? 'P0' : 'P1'}
                  </Badge>
                </div>
                <div className="flex items-center gap-1.5">
                  <span
                    className={cn(
                      'w-1.5 h-1.5 rounded-full shrink-0',
                      alert.level === 'critical' ? 'bg-danger' : 'bg-warning'
                    )}
                  />
                  <span className="text-xs text-text-subtle flex-1">{alert.msg}</span>
                </div>
                {alert.timestamp && (
                  <div className="text-[10px] text-text-subtle/70 mt-1.5 ml-3">
                    {alert.timestamp}
                  </div>
                )}
              </div>
            ))}
            {onViewAll && (
              <Button
                variant="outline"
                size="sm"
                onClick={onViewAll}
                className="w-full mt-3 text-xs border-dashed border-border-muted text-text-muted hover:text-text-body hover:border-border-default"
              >
                查看全部预警
                <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

