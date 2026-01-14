/**
 * SupplierCostTable - 渠道成本分析表格
 *
 * 显示每个渠道的费率、消耗、服务费等信息
 *
 * @module features/finance/components/ProfitAnalysis
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { SupplierCostItem, SupplierCostSummary } from '../../types/finance.types';
import { formatCurrency, formatPercent } from '../../utils/financeHelpers';

interface SupplierCostTableProps {
  items: SupplierCostItem[];
  summary: SupplierCostSummary;
}

export function SupplierCostTable({ items, summary }: SupplierCostTableProps) {

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">渠道成本分析</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>渠道</TableHead>
                <TableHead className="text-right">费率</TableHead>
                <TableHead className="text-right">本月消耗</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center text-muted-foreground py-4">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.supplier_id}>
                    <TableCell>
                      <div className="font-medium">{item.supplier_name}</div>
                      {item.platform && (
                        <div className="text-xs text-muted-foreground">{item.platform}</div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{formatPercent(item.fee_rate)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(item.total_spend)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* 汇总 */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">平均费率:</span>
            <span className="font-medium">{formatPercent(summary.avg_fee_rate)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
