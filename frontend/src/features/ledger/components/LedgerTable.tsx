/**
 * Ledger Table Component
 *
 * SoT: LEDGER_SOT.md v1.1
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
import { useLedgerEntries } from '../hooks';
import { ENTRY_TYPE_CONFIG } from '../types';
import type { LedgerListParams } from '../types';

export function LedgerTable() {
  const [params, setParams] = useState<LedgerListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useLedgerEntries(params);

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const formatAmount = (amount: number) => {
    return `¥${(amount / 100).toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
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

  const entries = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>时间</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>金额</TableHead>
            <TableHead>余额变化</TableHead>
            <TableHead>描述</TableHead>
            <TableHead>状态</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            entries.map((entry) => {
              const typeConfig = ENTRY_TYPE_CONFIG[entry.entry_type];
              return (
                <TableRow key={entry.id}>
                  <TableCell className="text-sm">
                    {formatDate(entry.created_at)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        typeConfig.variant === 'success'
                          ? 'default'
                          : typeConfig.variant === 'error'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {typeConfig.label}
                    </Badge>
                  </TableCell>
                  <TableCell
                    className={
                      typeConfig.direction === 'in'
                        ? 'text-green-600 font-medium'
                        : typeConfig.direction === 'out'
                        ? 'text-red-600 font-medium'
                        : 'font-medium'
                    }
                  >
                    {typeConfig.direction === 'in' && '+'}
                    {typeConfig.direction === 'out' && '-'}
                    {formatAmount(Number(entry.amount))}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatAmount(Number(entry.tenant_balance_before))} →{' '}
                    {formatAmount(Number(entry.tenant_balance_after))}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {entry.description}
                  </TableCell>
                  <TableCell>
                    {entry.is_locked ? (
                      <Badge variant="outline">已锁定</Badge>
                    ) : (
                      <Badge variant="secondary">活跃</Badge>
                    )}
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
