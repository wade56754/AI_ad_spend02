/**
 * ReconciliationDataTable - 对账批次表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { MoreHorizontal, Eye, CheckCircle, Edit } from 'lucide-react';
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
import type { ReconciliationBatch } from '../types';
import { RECONCILIATION_BATCH_STATUS_CONFIG } from '../types';

interface ReconciliationDataTableProps {
  batches: ReconciliationBatch[];
  loading?: boolean;
  onRowClick?: (batch: ReconciliationBatch) => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

export function ReconciliationDataTable({
  batches,
  loading,
  onRowClick,
  className,
}: ReconciliationDataTableProps) {
  const columns: ColumnDef<ReconciliationBatch>[] = [
    {
      key: 'batch_id',
      header: '批次号',
      render: (_, row) => (
        <span className="font-mono text-text-strong">{row.batch_id}</span>
      ),
    },
    {
      key: 'reconciliation_date',
      header: '对账日期',
      width: '120px',
      render: (_, row) => (
        <span className="text-text-body">{row.reconciliation_date}</span>
      ),
    },
    {
      key: 'ad_account_name',
      header: '账户',
      render: (_, row) => (
        <span className="text-text-body">{row.ad_account_name}</span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '100px',
      render: (_, row) => {
        const config = RECONCILIATION_BATCH_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'platform_amount',
      header: '平台金额',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          ¥{(row.platform_amount / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'system_amount',
      header: '系统金额',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          ¥{(row.system_amount / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'diff_amount',
      header: '差异',
      align: 'right',
      render: (_, row) => {
        const diff = row.platform_amount - row.system_amount;
        if (diff === 0) {
          return <span className="text-text-muted">-</span>;
        }
        return (
          <span className={cn(
            'font-medium',
            diff > 0 ? 'text-danger' : 'text-success'
          )}>
            {diff > 0 ? '+' : ''}¥{(diff / 100).toLocaleString()}
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
            {row.status === 'has_diff' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-text-body hover:bg-elevated">
                  <Edit className="mr-2 h-4 w-4" />
                  处理差异
                </DropdownMenuItem>
                <DropdownMenuItem className="text-success hover:bg-elevated">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  标记已解决
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
      data={batches}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无对账批次"
      title="对账批次"
      description={`共 ${batches.length} 个批次`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default ReconciliationDataTable;
