/**
 * ProjectProfitTable - 项目利润明细表格
 *
 * 显示每个项目的进粉、收入、成本、利润、利润率，包含利润状态标记
 *
 * @module features/finance/components/ProfitAnalysis
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
import type { ProjectProfitItem, ProfitStatus } from '../../types/finance.types';

interface ProjectProfitTableProps {
  items: ProjectProfitItem[];
}

const STATUS_ICONS: Record<ProfitStatus, string> = {
  healthy: '🟢',
  warning: '🟡',
  danger: '🔴',
  inactive: '⚫',
};

const STATUS_LABELS: Record<ProfitStatus, string> = {
  healthy: '健康',
  warning: '关注',
  danger: '警告',
  inactive: '非活跃',
};

export function ProjectProfitTable({ items }: ProjectProfitTableProps) {
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;
  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">项目利润排行</h3>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">状态</TableHead>
              <TableHead>项目</TableHead>
              <TableHead className="text-right">进粉</TableHead>
              <TableHead className="text-right">收入</TableHead>
              <TableHead className="text-right">成本</TableHead>
              <TableHead className="text-right">利润</TableHead>
              <TableHead className="text-right">利润率</TableHead>
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
                    <span title={STATUS_LABELS[item.profit_status]}>
                      {STATUS_ICONS[item.profit_status]}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{item.project_name}</div>
                    <div className="text-xs text-muted-foreground">
                      单价${item.avg_unit_price.toFixed(0)} | 费率{formatPercent(item.fee_rate)}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {item.conversions !== null ? item.conversions : '-'}
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(item.revenue)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(item.cost)}</TableCell>
                  <TableCell className="text-right">
                    <span className={item.profit < 0 ? 'text-red-500' : 'text-green-500'}>
                      {formatCurrency(item.profit)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={
                        item.profit_rate >= 0.15
                          ? 'text-green-500'
                          : item.profit_rate >= 0.05
                          ? 'text-amber-500'
                          : 'text-red-500'
                      }
                    >
                      {formatPercent(item.profit_rate)}
                    </span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
