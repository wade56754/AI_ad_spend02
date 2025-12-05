/**
 * AdAccountsDataTable - 广告账户列表表格
 *
 * 特性：
 * - 响应式表格布局
 * - 统一的货币格式化（¥12,345.00）
 * - 右对齐金额字段
 * - 空状态、加载状态支持
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { MoreHorizontal, ExternalLink, RefreshCw, DollarSign, FileSearch } from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/utils/formatters';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ModuleDataTable, type ColumnDef } from '@/modules/shared';
import type { AdAccount } from '../types';
import { AD_ACCOUNT_STATUS_CONFIG, PLATFORM_CONFIG } from '../types';

interface AdAccountsDataTableProps {
  accounts: AdAccount[];
  loading?: boolean;
  isEmpty?: boolean;
  onRowClick?: (account: AdAccount) => void;
  onRefresh?: () => void;
  className?: string;
}

const statusVariantMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  success: 'default',
  warning: 'secondary',
  error: 'destructive',
  info: 'outline',
  default: 'outline',
};

const riskColors: Record<string, string> = {
  low: 'text-success',
  medium: 'text-warning',
  high: 'text-danger',
};

const riskLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
};

export function AdAccountsDataTable({
  accounts,
  loading,
  isEmpty,
  onRowClick,
  onRefresh,
  className,
}: AdAccountsDataTableProps) {
  const columns: ColumnDef<AdAccount>[] = [
    {
      key: 'account_name',
      header: '账户名称',
      render: (_, row) => (
        <div className="min-w-[160px]">
          <div className="font-medium text-text-strong truncate">{row.account_name}</div>
          <div className="text-xs text-text-muted font-mono">{row.account_id}</div>
        </div>
      ),
    },
    {
      key: 'platform',
      header: '平台',
      width: '100px',
      render: (_, row) => {
        const config = PLATFORM_CONFIG[row.platform];
        return (
          <span className={cn('font-medium', config.color)}>
            {config.label}
          </span>
        );
      },
    },
    {
      key: 'status',
      header: '状态',
      width: '100px',
      render: (_, row) => {
        const config = AD_ACCOUNT_STATUS_CONFIG[row.status];
        return (
          <Badge variant={statusVariantMap[config.variant]}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      key: 'project_name',
      header: '关联项目',
      render: (_, row) => (
        <span className="text-text-body truncate max-w-[150px] block">
          {row.project_name || '-'}
        </span>
      ),
    },
    {
      key: 'balance',
      header: '余额',
      align: 'right',
      width: '120px',
      render: (_, row) => (
        <span className="text-text-body font-mono tabular-nums">
          ¥{formatMoney(row.balance)}
        </span>
      ),
    },
    {
      key: 'spent_today',
      header: '今日消耗',
      align: 'right',
      width: '120px',
      render: (_, row) => (
        <span className="text-text-body font-mono tabular-nums">
          ¥{formatMoney(row.spent_today)}
        </span>
      ),
    },
    {
      key: 'risk_level',
      header: '风险',
      align: 'center',
      width: '80px',
      render: (_, row) => {
        const level = row.risk_level || 'low';
        return (
          <span className={cn('font-medium', riskColors[level])}>
            {riskLabels[level]}
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
            <DropdownMenuItem
              className="text-text-body hover:bg-elevated cursor-pointer"
              onClick={(e) => {
                e.stopPropagation();
                onRowClick?.(row);
              }}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem className="text-text-body hover:bg-elevated cursor-pointer">
              <RefreshCw className="mr-2 h-4 w-4" />
              同步数据
            </DropdownMenuItem>
            <DropdownMenuItem className="text-text-body hover:bg-elevated cursor-pointer">
              <DollarSign className="mr-2 h-4 w-4" />
              充值
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  // Empty state component
  const emptyState = isEmpty ? (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 rounded-full bg-elevated mb-4">
        <FileSearch className="w-8 h-8 text-text-muted" />
      </div>
      <h3 className="text-lg font-semibold text-text-strong mb-2">
        暂无账户数据
      </h3>
      <p className="text-text-muted mb-4 max-w-md">
        当前筛选条件下没有找到广告账户，请尝试调整筛选条件或添加新账户
      </p>
      {onRefresh && (
        <Button
          variant="outline"
          onClick={onRefresh}
          className="gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          刷新列表
        </Button>
      )}
    </div>
  ) : undefined;

  return (
    <ModuleDataTable
      columns={columns}
      data={accounts}
      getRowKey={(row) => row.id}
      loading={loading}
      emptyText="暂无账户数据"
      emptyState={emptyState}
      title="账户列表"
      description={`共 ${accounts.length} 个账户`}
      onRowClick={onRowClick}
      className={className}
    />
  );
}

export default AdAccountsDataTable;
