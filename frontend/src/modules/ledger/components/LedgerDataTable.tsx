/**
 * LedgerDataTable - 账本流水表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, LEDGER_SOT.md v1.1
 */

'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownRight, MoreHorizontal, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ModuleDataTable, type ColumnDef } from '@/modules/shared';
import type { LedgerEntry } from '../types';
import { LEDGER_ENTRY_TYPE_CONFIG } from '../types';

interface LedgerDataTableProps {
  entries: LedgerEntry[];
  loading?: boolean;
  onRowClick?: (entry: LedgerEntry) => void;
  className?: string;
}

export function LedgerDataTable({
  entries,
  loading,
  onRowClick,
  className,
}: LedgerDataTableProps) {
  const columns: ColumnDef<LedgerEntry>[] = [
    {
      key: 'created_at',
      header: '时间',
      width: '160px',
      render: (_, row) => (
        <span className="text-text-muted text-sm">
          {new Date(row.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'entry_type',
      header: '类型',
      width: '100px',
      render: (_, row) => {
        const config = LEDGER_ENTRY_TYPE_CONFIG[row.entry_type];
        return (
          <Badge variant="outline" className={cn('border-border-default', config.color)}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'description',
      header: '描述',
      render: (_, row) => (
        <div>
          <div className="text-text-body">{row.description}</div>
          {row.reference_id && (
            <div className="text-xs text-text-muted">Ref: {row.reference_id.slice(0, 8)}...</div>
          )}
        </div>
      ),
    },
    {
      key: 'ad_account_name',
      header: '账户',
      render: (_, row) => (
        <span className="text-text-body">{row.ad_account_name || '-'}</span>
      ),
    },
    {
      key: 'amount',
      header: '金额',
      align: 'right',
      render: (_, row) => {
        const isCredit = row.amount > 0;
        return (
          <div className="flex items-center justify-end gap-1">
            {isCredit ? (
              <ArrowUpRight className="w-4 h-4 text-success" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-danger" />
            )}
            <span className={cn(
              'font-semibold',
              isCredit ? 'text-success' : 'text-danger'
            )}>
              {isCredit ? '+' : ''}¥{(row.amount / 100).toLocaleString()}
            </span>
          </div>
        );
      },
    },
    {
      key: 'balance_after',
      header: '余额',
      align: 'right',
      render: (_, row) => (
        <span className="text-text-body">
          ¥{(row.balance_after / 100).toLocaleString()}
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
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <ModuleDataTable
      columns={columns}
      data={entries}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无流水记录"
      title="账本流水"
      description={`共 ${entries.length} 条记录`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default LedgerDataTable;
