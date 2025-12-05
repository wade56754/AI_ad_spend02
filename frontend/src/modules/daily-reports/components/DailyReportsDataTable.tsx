/**
 * DailyReportsDataTable - 日报列表表格
 *
 * 显示日报列表，支持 8 状态流转
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, STATE_MACHINE.md v2.6
 */

'use client';

import React from 'react';
import { MoreHorizontal, Eye, CheckCircle, AlertTriangle, Lock } from 'lucide-react';
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
import type { DailyReport } from '../types';
import { STATUS_CONFIG } from '../types';

interface DailyReportsDataTableProps {
  reports: DailyReport[];
  loading?: boolean;
  onRowClick?: (report: DailyReport) => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

export function DailyReportsDataTable({
  reports,
  loading,
  onRowClick,
  className,
}: DailyReportsDataTableProps) {
  const columns: ColumnDef<DailyReport>[] = [
    {
      key: 'report_date',
      header: '日期',
      width: '120px',
      render: (_, row) => (
        <span className="font-medium text-text-strong">{row.report_date}</span>
      ),
    },
    {
      key: 'project_id',
      header: '项目',
      render: (_, row) => (
        <span className="text-text-body">{row.project_id}</span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '120px',
      render: (_, row) => {
        const config = STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'raw_spend',
      header: '原始消耗',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          ¥{(row.raw_spend / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'raw_impressions',
      header: '展示',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          {row.raw_impressions.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'raw_clicks',
      header: '点击',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          {row.raw_clicks.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'trend_alert_level',
      header: '趋势',
      align: 'center',
      width: '80px',
      render: (_, row) => {
        if (!row.trend_alert_level) return <span className="text-text-muted">-</span>;

        const colors: Record<string, string> = {
          normal: 'text-success',
          warning: 'text-warning',
          critical: 'text-danger',
        };

        return (
          <span className={cn('font-medium', colors[row.trend_alert_level])}>
            {row.trend_alert_level === 'normal' ? '正常' :
             row.trend_alert_level === 'warning' ? '警告' : '严重'}
          </span>
        );
      },
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
            {row.status === 'trend_pending' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-success hover:bg-elevated">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  通过趋势
                </DropdownMenuItem>
                <DropdownMenuItem className="text-warning hover:bg-elevated">
                  <AlertTriangle className="mr-2 h-4 w-4" />
                  标记异常
                </DropdownMenuItem>
              </>
            )}
            {row.status === 'final_confirmed' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-text-body hover:bg-elevated">
                  <Lock className="mr-2 h-4 w-4" />
                  锁定
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
      data={reports}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无日报数据"
      title="日报列表"
      description={`共 ${reports.length} 条日报`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default DailyReportsDataTable;
