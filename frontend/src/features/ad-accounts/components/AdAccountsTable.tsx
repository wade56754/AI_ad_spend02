/**
 * Ad Accounts Table Component
 *
 * SoT 对齐: STATE_MACHINE.md v2.6 Section 7
 * 对齐: init_schema.sql §5.1 ad_accounts 表
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
import { MoreHorizontal, PlayCircle, PauseCircle, Archive, Skull } from 'lucide-react';
import { useAdAccounts, useUpdateAdAccountStatus } from '../hooks';
import { AD_ACCOUNT_STATUS_CONFIG, ALLOWED_TRANSITIONS } from '../types';
import type { AdAccount, AdAccountListParams, AdAccountStatus } from '../types';

export function AdAccountsTable() {
  const [params, setParams] = useState<AdAccountListParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error } = useAdAccounts(params);
  const statusMutation = useUpdateAdAccountStatus();

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const handleStatusChange = (id: number, status: AdAccountStatus) => {
    statusMutation.mutate({
      id: String(id),
      input: { status },
    });
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

  const accounts = data?.items ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>账户名称</TableHead>
            <TableHead>项目ID</TableHead>
            <TableHead>渠道ID</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>创建时间</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {accounts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            accounts.map((account) => {
              const status = account.status ?? 'new';
              const statusConfig = AD_ACCOUNT_STATUS_CONFIG[status];
              const allowedTransitions = ALLOWED_TRANSITIONS[status] || [];
              return (
                <TableRow key={account.id}>
                  <TableCell className="font-medium">{account.name || '-'}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {account.project_id}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {account.channel_id ? account.channel_id.slice(0, 8) + '...' : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        statusConfig.variant === 'success'
                          ? 'default'
                          : statusConfig.variant === 'error'
                          ? 'destructive'
                          : statusConfig.variant === 'warning'
                          ? 'outline'
                          : 'secondary'
                      }
                    >
                      {statusConfig.label}
                    </Badge>
                    {account.status_reason && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({account.status_reason})
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(account.created_at).toLocaleDateString('zh-CN')}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {allowedTransitions.includes('testing') && (
                          <DropdownMenuItem
                            onClick={() => handleStatusChange(account.id, 'testing')}
                            disabled={statusMutation.isPending}
                          >
                            <PlayCircle className="mr-2 h-4 w-4" />
                            开始测试
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('active') && (
                          <DropdownMenuItem
                            onClick={() => handleStatusChange(account.id, 'active')}
                            disabled={statusMutation.isPending}
                          >
                            <PlayCircle className="mr-2 h-4 w-4" />
                            激活
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('suspended') && (
                          <DropdownMenuItem
                            onClick={() => handleStatusChange(account.id, 'suspended')}
                            disabled={statusMutation.isPending}
                          >
                            <PauseCircle className="mr-2 h-4 w-4" />
                            暂停
                          </DropdownMenuItem>
                        )}
                        {allowedTransitions.includes('dead') && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleStatusChange(account.id, 'dead')}
                              disabled={statusMutation.isPending}
                              className="text-destructive"
                            >
                              <Skull className="mr-2 h-4 w-4" />
                              标记死号
                            </DropdownMenuItem>
                          </>
                        )}
                        {allowedTransitions.includes('archived') && (
                          <DropdownMenuItem
                            onClick={() => handleStatusChange(account.id, 'archived')}
                            disabled={statusMutation.isPending}
                          >
                            <Archive className="mr-2 h-4 w-4" />
                            归档
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
