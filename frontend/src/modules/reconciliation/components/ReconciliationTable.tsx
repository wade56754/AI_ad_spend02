/**
 * Reconciliation Table Component
 *
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
import { Badge } from '@/components/ui/badge';
import { useReconciliations } from '../hooks';
import { RECONCILIATION_STATUS_CONFIG, RECONCILIATION_TYPE_CONFIG } from '../types';
import type { ReconciliationListParams } from '../types';

export function ReconciliationTable() {
  const [params, setParams] = useState<ReconciliationListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useReconciliations(params);

  const handlePageChange = (newPage: number) => {
    setParams((prev) => ({ ...prev, page: newPage }));
  };

  const formatAmount = (amount: number) => {
    return `¥${(amount / 100).toFixed(2)}`;
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

  const reconciliations = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>对账周期</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>预期消耗</TableHead>
            <TableHead>实际消耗</TableHead>
            <TableHead>差异</TableHead>
            <TableHead>状态</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reconciliations.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            reconciliations.map((recon) => {
              const statusConfig = RECONCILIATION_STATUS_CONFIG[recon.status];
              const typeConfig = RECONCILIATION_TYPE_CONFIG[recon.type];
              return (
                <TableRow key={recon.id}>
                  <TableCell className="font-medium">
                    {recon.period_start} ~ {recon.period_end}
                  </TableCell>
                  <TableCell>{typeConfig.label}</TableCell>
                  <TableCell>{formatAmount(recon.expected_spend as number)}</TableCell>
                  <TableCell>{formatAmount(recon.actual_spend as number)}</TableCell>
                  <TableCell
                    className={
                      recon.threshold_exceeded
                        ? 'text-red-600 font-medium'
                        : 'text-muted-foreground'
                    }
                  >
                    {formatAmount(recon.discrepancy as number)} (
                    {recon.discrepancy_percentage.toFixed(2)}%)
                    {recon.threshold_exceeded && (
                      <Badge variant="destructive" className="ml-2">
                        超阈值
                      </Badge>
                    )}
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
