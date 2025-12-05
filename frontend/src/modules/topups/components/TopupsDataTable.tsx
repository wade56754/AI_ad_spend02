/**
 * TopupsDataTable - 充值列表表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { MoreHorizontal, Eye, CheckCircle, XCircle } from 'lucide-react';
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
import type { Topup } from '../types';
import { TOPUP_STATUS_CONFIG } from '../types';

interface TopupsDataTableProps {
  topups: Topup[];
  loading?: boolean;
  onRowClick?: (topup: Topup) => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

export function TopupsDataTable({
  topups,
  loading,
  onRowClick,
  className,
}: TopupsDataTableProps) {
  const columns: ColumnDef<Topup>[] = [
    {
      key: 'id',
      header: '充值单号',
      render: (_, row) => (
        <span className="font-mono text-text-strong">{row.id.slice(0, 8)}...</span>
      ),
    },
    {
      key: 'ad_account_name',
      header: '账户',
      render: (_, row) => (
        <div>
          <div className="font-medium text-text-strong">{row.ad_account_name}</div>
          <div className="text-xs text-text-muted">{row.ad_account_id}</div>
        </div>
      ),
    },
    {
      key: 'amount',
      header: '金额',
      align: 'right',
      render: (_, row) => (
        <span className="font-semibold text-success">
          +¥{(row.amount / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '100px',
      render: (_, row) => {
        const config = TOPUP_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'requested_by',
      header: '申请人',
      render: (_, row) => (
        <span className="text-text-body">{row.requested_by}</span>
      ),
    },
    {
      key: 'created_at',
      header: '申请时间',
      render: (_, row) => (
        <span className="text-text-muted text-sm">
          {new Date(row.created_at).toLocaleDateString()}
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
            {row.status === 'pending' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-success hover:bg-elevated">
                  <CheckCircle className="mr-2 h-4 w-4" />
                  审批通过
                </DropdownMenuItem>
                <DropdownMenuItem className="text-danger hover:bg-elevated">
                  <XCircle className="mr-2 h-4 w-4" />
                  拒绝
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
      data={topups}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无充值记录"
      title="充值列表"
      description={`共 ${topups.length} 条记录`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default TopupsDataTable;
