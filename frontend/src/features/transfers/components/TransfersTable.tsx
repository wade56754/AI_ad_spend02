/**
 * Transfers Table Component
 *
 * SoT 对齐: STATE_MACHINE.md v2.6 第12章
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  MoreHorizontal,
  Send,
  CheckCircle,
  XCircle,
  PlayCircle,
} from 'lucide-react';
import {
  useTransfers,
  useSubmitTransfer,
  useApproveTransfer,
  useRejectTransfer,
  useCompleteTransfer,
} from '../hooks';
import {
  TRANSFER_STATUS_CONFIG,
  TRANSFER_ALLOWED_TRANSITIONS,
} from '../types';
import type { Transfer, TransferListParams } from '../types';

export function TransfersTable() {
  const [params, setParams] = useState<TransferListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useTransfers(params);
  const submitMutation = useSubmitTransfer();
  const approveMutation = useApproveTransfer();
  const rejectMutation = useRejectTransfer();
  const completeMutation = useCompleteTransfer();

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const handleSubmit = (id: number) => {
    submitMutation.mutate(id);
  };

  const handleApprove = (id: number) => {
    approveMutation.mutate({ id, input: {} });
  };

  const handleReject = (id: number) => {
    const reason = prompt('请输入拒绝原因');
    if (reason) {
      rejectMutation.mutate({ id, input: { rejection_reason: reason } });
    }
  };

  const handleComplete = (id: number) => {
    completeMutation.mutate(id);
  };

  const isPending =
    submitMutation.isPending ||
    approveMutation.isPending ||
    rejectMutation.isPending ||
    completeMutation.isPending;

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

  const transfers = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>申请编号</TableHead>
            <TableHead>源账户</TableHead>
            <TableHead>目标账户</TableHead>
            <TableHead className="text-right">迁移金额</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transfers.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            transfers.map((transfer: Transfer) => {
              const statusConfig = TRANSFER_STATUS_CONFIG[transfer.status];
              const allowedTransitions = TRANSFER_ALLOWED_TRANSITIONS[transfer.status] || [];
              return (
                <TableRow key={transfer.id}>
                  <TableCell className="font-mono text-sm">
                    {transfer.request_no}
                  </TableCell>
                  <TableCell>
                    {transfer.source_ad_account_name || `ID: ${transfer.source_ad_account_id}`}
                  </TableCell>
                  <TableCell>
                    {transfer.target_ad_account_name || `ID: ${transfer.target_ad_account_id}`}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    ¥{parseFloat(transfer.transfer_amount).toLocaleString('zh-CN', {
                      minimumFractionDigits: 2,
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusConfig.variant}>
                      {statusConfig.label}
                    </Badge>
                    {transfer.rejection_reason && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({transfer.rejection_reason})
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(transfer.created_at).toLocaleDateString('zh-CN')}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {allowedTransitions.includes('pending_approval') && (
                          <DropdownMenuItem
                            onClick={() => handleSubmit(transfer.id)}
                            disabled={isPending}
                          >
                            <Send className="mr-2 h-4 w-4" />
                            提交审批
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('approved') && (
                          <DropdownMenuItem
                            onClick={() => handleApprove(transfer.id)}
                            disabled={isPending}
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            审批通过
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('completed') && (
                          <DropdownMenuItem
                            onClick={() => handleComplete(transfer.id)}
                            disabled={isPending}
                          >
                            <PlayCircle className="mr-2 h-4 w-4" />
                            完成迁移
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('rejected') && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleReject(transfer.id)}
                              disabled={isPending}
                              className="text-destructive"
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              拒绝
                            </DropdownMenuItem>
                          </>
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
