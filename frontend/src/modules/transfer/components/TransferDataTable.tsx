/**
 * TransferDataTable - 迁移申请表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, TRANSFER_SOT.md v1.0
 */

'use client';

import React from 'react';
import { MoreHorizontal, Eye, CheckCircle, XCircle, Play } from 'lucide-react';
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
import type { TransferRequest, TransferStatus } from '../types';
import { TRANSFER_STATUS_CONFIG } from '../types';

interface TransferDataTableProps {
  transfers: TransferRequest[];
  loading?: boolean;
  onRowClick?: (transfer: TransferRequest) => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

export function TransferDataTable({
  transfers,
  loading,
  onRowClick,
  className,
}: TransferDataTableProps) {
  const columns: ColumnDef<TransferRequest>[] = [
    {
      key: 'request_no',
      header: '申请单号',
      render: (_, row) => (
        <span className="font-mono text-text-strong">{row.request_no}</span>
      ),
    },
    {
      key: 'source',
      header: '源账户',
      render: (_, row) => (
        <div>
          <p className="text-text-body">{row.source_ad_account_name}</p>
          <p className="text-xs text-text-muted">{row.supplier_name}</p>
        </div>
      ),
    },
    {
      key: 'target',
      header: '目标账户',
      render: (_, row) => (
        <span className="text-text-body">{row.target_ad_account_name}</span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      width: '100px',
      render: (_, row) => {
        const config = TRANSFER_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'transfer_amount',
      header: '迁移金额',
      align: 'right',
      render: (_, row) => (
        <span className="font-medium text-text-strong">
          ¥{(row.transfer_amount / 100).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'created_by_name',
      header: '发起人',
      width: '100px',
      render: (_, row) => (
        <span className="text-text-body">{row.created_by_name}</span>
      ),
    },
    {
      key: 'created_at',
      header: '创建时间',
      width: '160px',
      render: (_, row) => (
        <span className="text-text-muted">
          {new Date(row.created_at).toLocaleString('zh-CN')}
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
            {row.status === 'draft' && (
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
            {row.status === 'approved' && (
              <>
                <DropdownMenuSeparator className="bg-border-default" />
                <DropdownMenuItem className="text-info hover:bg-elevated">
                  <Play className="mr-2 h-4 w-4" />
                  执行迁移
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
      data={transfers}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无迁移申请"
      title="迁移申请列表"
      description={`共 ${transfers.length} 条记录`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default TransferDataTable;
