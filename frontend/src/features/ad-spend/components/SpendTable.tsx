/**
 * SpendTable Component
 *
 * SoT: docs/10.module-specs/C3-spend-detail.md §3.1
 * CodeBlock: CB-FE-001 (DataTable)
 *
 * 功能: 消耗明细数据表格
 */

'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { AdSpendRecord } from '../types';

export interface SpendTableProps {
  data: AdSpendRecord[];
  total: number;
  page: number;
  pageSize: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('zh-CN').format(value);
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 flex-1" />
        </div>
      ))}
    </div>
  );
}

export function SpendTable({
  data,
  total,
  page,
  pageSize,
  loading,
  onPageChange,
}: SpendTableProps) {
  const totalPages = Math.ceil(total / pageSize);
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, total);

  return (
    <Card>
      <CardHeader>
        <CardTitle>消耗明细</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <TableSkeleton />
        ) : data.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground">
            暂无数据
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>账户</TableHead>
                    <TableHead>项目</TableHead>
                    <TableHead>渠道</TableHead>
                    <TableHead>日期</TableHead>
                    <TableHead className="text-right">消耗</TableHead>
                    <TableHead className="text-right">曝光</TableHead>
                    <TableHead className="text-right">点击</TableHead>
                    <TableHead className="text-right">粉数</TableHead>
                    <TableHead className="text-right">CTR</TableHead>
                    <TableHead className="text-right">CPA</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        {item.ad_account_name}
                      </TableCell>
                      <TableCell>{item.project_name}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{item.channel_name}</Badge>
                      </TableCell>
                      <TableCell>{item.report_date}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(item.spend)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatNumber(item.impressions)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatNumber(item.clicks)}
                      </TableCell>
                      <TableCell className="text-right font-medium text-green-600">
                        {item.conversions}
                      </TableCell>
                      <TableCell className="text-right">
                        {(item.ctr ?? 0).toFixed(2)}%
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.cpa)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                显示 {startIndex}-{endIndex} 共 {total} 条
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(page - 1)}
                  disabled={page <= 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange(page + 1)}
                  disabled={page >= totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default SpendTable;
