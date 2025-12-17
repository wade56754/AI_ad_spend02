/**
 * Topups Table Component
 *
 * Enhanced table with 7-state workflow support
 * SoT: STATE_MACHINE.md v2.6 Section 9
 */

'use client';

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  MoreHorizontal,
  Eye,
  Send,
  ClipboardCheck,
  Wallet,
  CheckCircle,
  Ban,
} from 'lucide-react';
import { useTopups } from '../hooks';
import { TopupStatusBadge, TopupAmount } from './TopupStatusBadge';
import type { TopupRequest, TopupListParams } from '../types';

interface TopupsTableProps {
  onViewDetail?: (topup: TopupRequest) => void;
}

export function TopupsTable({ onViewDetail }: TopupsTableProps) {
  const [params, setParams] = useState<TopupListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useTopups(params);

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  // Handle Money type - could be number or object
  const getAmountValue = (amount: TopupRequest['amount']): number => {
    if (typeof amount === 'number') return amount;
    return (amount as { value?: number })?.value ?? 0;
  };

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>;
  }

  if (error) {
    return (
      <div className="py-8 text-center text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  const topups = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  // Get available quick actions for a topup based on status
  const getQuickActions = (topup: TopupRequest) => {
    const actions: Array<{
      icon: typeof Eye;
      label: string;
      action: string;
      variant?: 'default' | 'destructive';
    }> = [];

    switch (topup.status) {
      case 'draft':
        actions.push({ icon: Send, label: '提交审批', action: 'submit' });
        actions.push({ icon: Ban, label: '取消申请', action: 'cancel', variant: 'destructive' });
        break;
      case 'pending_review':
        actions.push({ icon: ClipboardCheck, label: '数据复核', action: 'data_review' });
        actions.push({ icon: Ban, label: '取消申请', action: 'cancel', variant: 'destructive' });
        break;
      case 'finance_approve':
        actions.push({ icon: Wallet, label: '财务终审', action: 'finance_approval' });
        actions.push({ icon: Ban, label: '取消申请', action: 'cancel', variant: 'destructive' });
        break;
      case 'paid':
        actions.push({ icon: CheckCircle, label: '确认到账', action: 'complete' });
        break;
    }

    return actions;
  };

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>申请时间</TableHead>
            <TableHead>项目</TableHead>
            <TableHead>广告账户</TableHead>
            <TableHead className="text-right">金额</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>申请人</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {topups.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                暂无充值申请
              </TableCell>
            </TableRow>
          ) : (
            topups.map((topup) => {
              const quickActions = getQuickActions(topup);
              const amountValue = getAmountValue(topup.amount);

              return (
                <TableRow
                  key={topup.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onViewDetail?.(topup)}
                >
                  <TableCell>{formatDate(topup.requested_at)}</TableCell>
                  <TableCell>
                    <div className="max-w-[120px] truncate">
                      {topup.project_name || topup.project_id.slice(0, 8)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-[120px] truncate">
                      {topup.ad_account_name || '-'}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <TopupAmount amount={amountValue} currency={topup.currency} />
                  </TableCell>
                  <TableCell>
                    <TopupStatusBadge status={topup.status} size="sm" showTooltip={false} />
                  </TableCell>
                  <TableCell>
                    <div className="max-w-[80px] truncate text-sm text-muted-foreground">
                      {topup.requested_by_name || '-'}
                    </div>
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onViewDetail?.(topup)}>
                          <Eye className="mr-2 h-4 w-4" />
                          查看详情
                        </DropdownMenuItem>

                        {quickActions.length > 0 && <DropdownMenuSeparator />}

                        {quickActions.map((action) => (
                          <DropdownMenuItem
                            key={action.action}
                            onClick={() => onViewDetail?.(topup)}
                            className={action.variant === 'destructive' ? 'text-destructive' : ''}
                          >
                            <action.icon className="mr-2 h-4 w-4" />
                            {action.label}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>

      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            共 {pagination.total} 条，第 {pagination.page} / {pagination.total_pages} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page <= 1}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page >= pagination.total_pages}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default TopupsTable;
