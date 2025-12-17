/**
 * Daily Reports Table Component
 *
 * SoT: STATE_MACHINE.md v2.6 Section 8 (8-state machine)
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
import { MoreHorizontal, Send, Check, Flag, Lock } from 'lucide-react';
import {
  useDailyReports,
  useSubmitForTrend,
  useApproveTrend,
  useSubmitForFinal,
  useLockReport,
} from '../hooks';
import { STATUS_CONFIG } from '../types';
import type { DailyReport, DailyReportListParams } from '../types';

export function DailyReportsTable() {
  const [params, setParams] = useState<DailyReportListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'report_date',
    sort_order: 'desc',
  });

  const { data, isLoading, error } = useDailyReports(params);
  const submitTrendMutation = useSubmitForTrend();
  const approveTrendMutation = useApproveTrend();
  const submitFinalMutation = useSubmitForFinal();
  const lockMutation = useLockReport();

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

  const reports = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>报告日期</TableHead>
            <TableHead>原始消耗</TableHead>
            <TableHead>展示</TableHead>
            <TableHead>点击</TableHead>
            <TableHead>转化</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="w-[80px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground">
                暂无数据
              </TableCell>
            </TableRow>
          ) : (
            reports.map((report) => {
              const statusConfig = STATUS_CONFIG[report.status];
              return (
                <TableRow key={report.id}>
                  <TableCell className="font-medium">{report.report_date}</TableCell>
                  <TableCell>{formatAmount(Number(report.raw_spend))}</TableCell>
                  <TableCell>{report.raw_impressions.toLocaleString()}</TableCell>
                  <TableCell>{report.raw_clicks.toLocaleString()}</TableCell>
                  <TableCell>{report.raw_conversions.toLocaleString()}</TableCell>
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
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {report.status === 'raw_submitted' && (
                          <DropdownMenuItem
                            onClick={() => submitTrendMutation.mutate(report.id)}
                            disabled={submitTrendMutation.isPending}
                          >
                            <Send className="mr-2 h-4 w-4" />
                            提交趋势审核
                          </DropdownMenuItem>
                        )}
                        {report.status === 'trend_pending' && (
                          <DropdownMenuItem
                            onClick={() => approveTrendMutation.mutate(report.id)}
                            disabled={approveTrendMutation.isPending}
                          >
                            <Check className="mr-2 h-4 w-4" />
                            趋势通过
                          </DropdownMenuItem>
                        )}
                        {(report.status === 'trend_ok' || report.status === 'trend_resolved') && (
                          <DropdownMenuItem
                            onClick={() => submitFinalMutation.mutate(report.id)}
                            disabled={submitFinalMutation.isPending}
                          >
                            <Send className="mr-2 h-4 w-4" />
                            提交终审
                          </DropdownMenuItem>
                        )}
                        {report.status === 'final_confirmed' && (
                          <DropdownMenuItem
                            onClick={() => lockMutation.mutate(report.id)}
                            disabled={lockMutation.isPending}
                          >
                            <Lock className="mr-2 h-4 w-4" />
                            锁定
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
