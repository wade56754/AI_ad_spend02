/**
 * ReceivablesTable - 应收账款明细表格
 *
 * 显示每个项目的打款、应收、已收、未收情况
 *
 * @module features/finance/components/FundOverview
 */

'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import type { ReceivableItem, ReceivablesTotals, ReceivableStatus } from '../../types/finance.types';

interface ReceivablesTableProps {
  items: ReceivableItem[];
  totals: ReceivablesTotals;
  onExport?: () => void;
}

const STATUS_CONFIG: Record<ReceivableStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
  settled: { label: '已结清', variant: 'default' },
  outstanding: { label: '待收款', variant: 'destructive' },
  refunded: { label: '已退款', variant: 'secondary' },
};

export function ReceivablesTable({ items, totals, onExport }: ReceivablesTableProps) {
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  const getStatusBadge = (status: ReceivableStatus, outstanding: number) => {
    const config = STATUS_CONFIG[status];
    if (status === 'refunded') {
      return <Badge variant="secondary">已退款</Badge>;
    }
    if (outstanding > 0) {
      return <Badge variant="destructive">待收 {formatCurrency(outstanding)}</Badge>;
    }
    return <Badge variant="default">已结清</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">应收账款明细</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onExport}>
            <Download className="mr-2 h-4 w-4" />
            导出Excel
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>甲方/项目</TableHead>
              <TableHead className="text-right">总打款</TableHead>
              <TableHead className="text-right">应收</TableHead>
              <TableHead className="text-right">已收</TableHead>
              <TableHead className="text-right">未收</TableHead>
              <TableHead className="text-right">余额</TableHead>
              <TableHead>状态</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                  暂无数据
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.project_id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{item.client_name}</div>
                      <div className="text-sm text-muted-foreground">{item.project_name}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(item.total_topup)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.total_receivable)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.total_received)}</TableCell>
                  <TableCell className="text-right">
                    {item.outstanding > 0 ? (
                      <span className="text-red-500 font-medium">
                        {formatCurrency(item.outstanding)}
                      </span>
                    ) : (
                      formatCurrency(0)
                    )}
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(item.balance)}</TableCell>
                  <TableCell>{getStatusBadge(item.status, item.outstanding)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* 汇总行 */}
      <div className="flex justify-end gap-8 text-sm">
        <div>
          <span className="text-muted-foreground">打款总额: </span>
          <span className="font-medium">{formatCurrency(totals.total_topup)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">应收总额: </span>
          <span className="font-medium">{formatCurrency(totals.total_receivable)}</span>
        </div>
        <div>
          <span className="text-muted-foreground">未收总额: </span>
          <span className="font-medium text-red-500">{formatCurrency(totals.total_outstanding)}</span>
        </div>
      </div>
    </div>
  );
}
