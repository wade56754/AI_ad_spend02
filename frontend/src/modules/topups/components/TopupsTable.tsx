/**
 * Topups Table Component
 *
 * SoT: STATE_MACHINE.md v2.6 Section 7
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
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Check, X, CheckCircle } from 'lucide-react';
import { useTopups, useApproveTopup, useRejectTopup, useCompleteTopup } from '../hooks';
import { TOPUP_STATUS_CONFIG } from '../types';
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
  const approveMutation = useApproveTopup();
  const rejectMutation = useRejectTopup();
  const completeMutation = useCompleteTopup();

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const handleApprove = (id: string) => {
    approveMutation.mutate({ id });
  };

  const handleReject = (id: string) => {
    rejectMutation.mutate({ id, input: { rejection_reason: '管理员拒绝' } });
  };

  const handleComplete = (id: string) => {
    completeMutation.mutate(id);
  };

  const formatAmount = (amount: number) => {
    return `¥${(amount / 100).toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
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

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>申请时间</TableHead>
            <TableHead>项目ID</TableHead>
            <TableHead>金额</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>备注</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {topups.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            topups.map((topup) => {
              const statusConfig = TOPUP_STATUS_CONFIG[topup.status];
              return (
                <TableRow key={topup.id}>
                  <TableCell>{formatDate(topup.requested_at)}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {topup.project_id.slice(0, 8)}...
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatAmount(topup.amount as number)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        statusConfig.variant === 'success'
                          ? 'default'
                          : statusConfig.variant === 'error'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {statusConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {topup.notes || '-'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {topup.status === 'pending' && (
                          <>
                            <DropdownMenuItem
                              onClick={() => handleApprove(topup.id)}
                              disabled={approveMutation.isPending}
                            >
                              <Check className="mr-2 h-4 w-4" />
                              审批通过
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleReject(topup.id)}
                              disabled={rejectMutation.isPending}
                              className="text-destructive"
                            >
                              <X className="mr-2 h-4 w-4" />
                              拒绝
                            </DropdownMenuItem>
                          </>
                        )}
                        {topup.status === 'approved' && (
                          <DropdownMenuItem
                            onClick={() => handleComplete(topup.id)}
                            disabled={completeMutation.isPending}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            完成充值
                          </DropdownMenuItem>
                        )}
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
