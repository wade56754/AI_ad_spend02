/**
 * RiskAlertDataTable - 风险预警表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { MoreHorizontal, Eye, CheckCircle, XCircle, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ModuleDataTable, type ColumnDef } from '@/modules/shared';
import type { RiskAlert } from '../types';
import { RISK_LEVEL_CONFIG, RISK_TYPE_CONFIG, ALERT_STATUS_CONFIG } from '../types';

interface RiskAlertDataTableProps {
  alerts: RiskAlert[];
  loading?: boolean;
  onRowClick?: (alert: RiskAlert) => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

const levelIndicatorMap: Record<string, string> = {
  critical: 'bg-danger',
  high: 'bg-warning',
  medium: 'bg-info',
  low: 'bg-text-muted',
};

export function RiskAlertDataTable({
  alerts,
  loading,
  onRowClick,
  className,
}: RiskAlertDataTableProps) {
  const columns: ColumnDef<RiskAlert>[] = [
    {
      key: 'risk_level',
      header: '级别',
      width: '60px',
      render: (_, row) => (
        <div className="flex items-center justify-center">
          <div className={cn(
            'h-3 w-3 rounded-full',
            levelIndicatorMap[row.risk_level]
          )} />
        </div>
      ),
    },
    {
      key: 'title',
      header: '预警内容',
      render: (_, row) => (
        <div>
          <p className="font-medium text-text-strong">{row.title}</p>
          <p className="text-xs text-text-muted line-clamp-1">{row.description}</p>
        </div>
      ),
    },
    {
      key: 'risk_type',
      header: '类型',
      width: '100px',
      render: (_, row) => (
        <span className="text-text-body">
          {RISK_TYPE_CONFIG[row.risk_type].label}
        </span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '90px',
      render: (_, row) => {
        const config = ALERT_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'target',
      header: '关联对象',
      render: (_, row) => (
        <div>
          {row.ad_account_name && (
            <p className="text-text-body">{row.ad_account_name}</p>
          )}
          {row.project_name && (
            <p className="text-xs text-text-muted">{row.project_name}</p>
          )}
        </div>
      ),
    },
    {
      key: 'deviation',
      header: '偏离度',
      align: 'right',
      width: '100px',
      render: (_, row) => {
        const isNegative = row.deviation_percentage < 0;
        return (
          <span className={cn(
            'font-medium',
            isNegative ? 'text-danger' : 'text-warning'
          )}>
            {isNegative ? '' : '+'}{row.deviation_percentage}%
          </span>
        );
      },
    },
    {
      key: 'detected_at',
      header: '检测时间',
      width: '160px',
      render: (_, row) => (
        <span className="text-text-muted">
          {new Date(row.detected_at).toLocaleString('zh-CN')}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '60px',
      align: 'right',
      render: (_, row) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 hover:bg-elevated"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4 text-text-muted" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="bg-card-bg border-border-default"
          >
            <DropdownMenuItem className="text-text-body hover:bg-elevated">
              <Eye className="mr-2 h-4 w-4" />
              查看详情
            </DropdownMenuItem>
            {row.status === 'active' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-info hover:bg-elevated">
                  <Bell className="mr-2 h-4 w-4" />
                  确认预警
                </DropdownMenuItem>
                <DropdownMenuItem className="text-success hover:bg-elevated">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  标记解决
                </DropdownMenuItem>
                <DropdownMenuItem className="text-text-muted hover:bg-elevated">
                  <XCircle className="mr-2 h-4 w-4" />
                  忽略
                </DropdownMenuItem>
              </>
            )}
            {row.status === 'acknowledged' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-success hover:bg-elevated">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  标记解决
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <ModuleDataTable
      columns={columns}
      data={alerts}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无风险预警"
      title="风险预警列表"
      description={`共 ${alerts.length} 条预警`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default RiskAlertDataTable;
