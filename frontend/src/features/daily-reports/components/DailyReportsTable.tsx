/**
 * Daily Reports Table Component - Refactored v2.1
 *
 * 优化版本：
 * - 数值列右对齐 + tabular-nums 等宽数字
 * - 日期列禁止换行
 * - 紧凑行高，提高数据密度
 * - 移除独立筛选栏（由父组件 DailyReportsPage 统一管理）
 *
 * SoT: STATE_MACHINE.md v2.6 Section 8 (8-state machine)
 */

'use client';

import { useState, memo, useCallback } from 'react';
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { MoreHorizontal, Send, Check, Lock, HelpCircle } from 'lucide-react';
import {
  useDailyReports,
  useSubmitForTrend,
  useApproveTrend,
  useSubmitForFinal,
  useLockReport,
} from '../hooks';
import { STATUS_CONFIG, PLATFORM_OPTIONS, REGION_OPTIONS } from '../types';
import type { DailyReport, DailyReportListParams, AdPlatform, AdRegion } from '../types';

// ============================================================================
// 类型定义
// ============================================================================

interface DailyReportsTableProps {
  filters?: DailyReportListParams;
  onFiltersChange?: (filters: DailyReportListParams) => void;
}

// ============================================================================
// 工具函数 - P0 金额精度修复
// ============================================================================

// Money 类型定义 (from @/types)
interface MoneyType {
  amount: number;
  currency: 'CNY' | 'USD';
}

/**
 * 格式化金额 - 精确到分 (避免浮点误差)
 * 支持 number | string | Money 类型
 * 使用 Math.round 保证分级精度
 */
const formatAmount = (
  amount: number | string | MoneyType | undefined,
  currency: string = 'USD'
): string => {
  if (amount === undefined || amount === null) return '-';

  let numAmount: number;
  let currencyCode = currency;

  // 处理 Money 对象类型
  if (typeof amount === 'object' && 'amount' in amount) {
    numAmount = amount.amount / 100; // 转换分为元
    currencyCode = amount.currency;
  } else {
    numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  }

  if (isNaN(numAmount)) return '-';
  // 精确到分：Math.round(x * 100) / 100
  const precise = Math.round(numAmount * 100) / 100;
  const symbol = currencyCode === 'CNY' ? '¥' : '$';
  // 强制 2 位小数
  return `${symbol}${precise.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
};

/**
 * 计算并格式化成本指标 - 精确到分
 * 支持 number | string | Money 类型
 */
const formatCostMetric = (
  spend: number | string | MoneyType | undefined,
  count: number,
  currency: string = 'USD'
): string => {
  if (spend === undefined || spend === null) return '-';

  let numSpend: number;
  let currencyCode = currency;

  // 处理 Money 对象类型
  if (typeof spend === 'object' && 'amount' in spend) {
    numSpend = spend.amount / 100; // 转换分为元
    currencyCode = spend.currency;
  } else {
    numSpend = typeof spend === 'string' ? parseFloat(spend) : spend;
  }

  if (isNaN(numSpend) || count === 0) return '-';
  // 精确到分：Math.round(spend * 100 / count) / 100
  const cost = Math.round((numSpend * 100) / count) / 100;
  const symbol = currencyCode === 'CNY' ? '¥' : '$';
  return `${symbol}${cost.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
};

/**
 * 格式化日期 - 返回结构化对象用于差异化渲染
 * 年份灰化 + 月日强调
 */
const formatDateParts = (dateStr: string): { year: string; monthDay: string } | null => {
  if (!dateStr) return null;
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    return { year: parts[0], monthDay: `${parts[1]}-${parts[2]}` };
  }
  return null;
};

const formatDate = (dateStr: string): string => {
  // 简化日期格式：MM-DD (向后兼容)
  if (!dateStr) return '-';
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    return `${parts[1]}-${parts[2]}`;
  }
  return dateStr;
};

const getPlatformLabel = (platform: AdPlatform | undefined): string => {
  if (!platform) return '-';
  const option = PLATFORM_OPTIONS.find(p => p.value === platform);
  return option?.label || platform;
};

const getRegionLabel = (region: AdRegion | undefined): string => {
  if (!region) return '-';
  const option = REGION_OPTIONS.find(r => r.value === region);
  return option?.label || region;
};

// ============================================================================
// 状态视觉配置 - v3.0 带色点 Badge
// ============================================================================

const STATUS_VISUAL: Record<string, { dot: string; bg: string; text: string }> = {
  raw_submitted:   { dot: 'bg-gray-400',   bg: 'bg-gray-50',    text: 'text-gray-700' },
  trend_pending:   { dot: 'bg-blue-500',   bg: 'bg-blue-50',    text: 'text-blue-700' },
  trend_ok:        { dot: 'bg-green-500',  bg: 'bg-green-50',   text: 'text-green-700' },
  trend_flagged:   { dot: 'bg-red-500',    bg: 'bg-red-50',     text: 'text-red-700' },
  trend_resolved:  { dot: 'bg-amber-500',  bg: 'bg-amber-50',   text: 'text-amber-700' },
  final_pending:   { dot: 'bg-purple-500', bg: 'bg-purple-50',  text: 'text-purple-700' },
  final_confirmed: { dot: 'bg-emerald-500',bg: 'bg-emerald-50', text: 'text-emerald-700' },
  final_locked:    { dot: 'bg-slate-600',  bg: 'bg-slate-100',  text: 'text-slate-700' },
};

// FE-P0-3 修复: 默认状态配置，防止未知状态导致崩溃
const DEFAULT_STATUS_CONFIG = { label: '未知', variant: 'default' as const };

const STATUS_TOOLTIP = `状态流程：
• 原始提交 → 趋势待审 → 趋势通过/异常
• 异常已处理 → 终审待审 → 终审确认 → 已锁定`;

// ============================================================================
// 主组件 - P1 性能优化：使用 React.memo 防止不必要重渲染
// ============================================================================

export const DailyReportsTable = memo(function DailyReportsTable({ filters, onFiltersChange }: DailyReportsTableProps) {
  // 内部 state（如果没有外部控制）
  const [internalParams, setInternalParams] = useState<DailyReportListParams>({
    page: 1,
    page_size: 20,
    sort_by: 'report_date',
    sort_order: 'desc',
  });

  // 使用外部 filters 或内部 params
  const params = filters || internalParams;
  const setParams = onFiltersChange || setInternalParams;

  // Data fetching
  const { data, isLoading, error } = useDailyReports(params);
  const submitTrendMutation = useSubmitForTrend();
  const approveTrendMutation = useApproveTrend();
  const submitFinalMutation = useSubmitForFinal();
  const lockMutation = useLockReport();

  // Handlers
  const handlePageChange = (newPage: number) => {
    setParams({ ...params, page: newPage });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <div className="animate-pulse">加载中...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center py-12 text-destructive">
        加载失败: {error.message}
      </div>
    );
  }

  const reports = data?.data ?? [];
  const pagination = data?.meta?.pagination;

  return (
    <TooltipProvider>
      <div className="space-y-2">
        {/* 表格 - v3.0 白色卡片 + 阴影 + 固定表头 */}
        <div className="rounded-xl border-0 bg-white shadow-sm overflow-hidden">
          <div className="max-h-[calc(100vh-320px)] overflow-y-auto overflow-x-auto">
            <Table>
              <TableHeader className="sticky top-0 z-10 bg-gray-50/80 backdrop-blur-sm border-b">
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[75px] whitespace-nowrap font-medium">日期</TableHead>
                  <TableHead className="w-[80px] font-medium">投手</TableHead>
                  <TableHead className="w-[80px] font-medium hidden md:table-cell">团队</TableHead>
                  <TableHead className="w-[70px] font-medium hidden lg:table-cell">地区</TableHead>
                  <TableHead className="w-[70px] font-medium hidden lg:table-cell">平台</TableHead>
                  <TableHead className="w-[100px] text-right font-medium font-mono">消耗</TableHead>
                  <TableHead className="w-[70px] text-right font-medium font-mono">进粉</TableHead>
                  <TableHead className="w-[70px] text-right font-medium font-mono">成效</TableHead>
                  <TableHead className="w-[90px] text-right font-medium font-mono hidden sm:table-cell">单粉成本</TableHead>
                  <TableHead className="w-[90px] text-right font-medium font-mono hidden sm:table-cell">成效费用</TableHead>
                  <TableHead className="w-[90px] font-medium">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <span className="inline-flex items-center gap-1 cursor-help">
                          状态
                          <HelpCircle className="h-3 w-3 text-muted-foreground" />
                        </span>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-[260px] text-xs whitespace-pre-line">
                        {STATUS_TOOLTIP}
                      </TooltipContent>
                    </Tooltip>
                  </TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
            <TableBody>
              {reports.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={12} className="h-24 text-center text-muted-foreground">
                    暂无数据
                  </TableCell>
                </TableRow>
              ) : (
                reports.map((report) => {
                  // FE-P0-3 修复: 使用默认值防止未知状态导致 undefined 崩溃
                  const statusConfig = STATUS_CONFIG[report.status] || DEFAULT_STATUS_CONFIG;
                  const currency = report.currency || 'USD';

                  return (
                    <TableRow key={report.id} className="h-9 hover:bg-gray-50/50">
                      {/* 日期 - 年份灰化 + 月日强调 */}
                      <TableCell className="whitespace-nowrap tabular-nums text-xs font-mono">
                        {(() => {
                          const dateParts = formatDateParts(report.report_date);
                          if (!dateParts) return '-';
                          return (
                            <span>
                              <span className="text-gray-400">{dateParts.year.slice(2)}-</span>
                              <span className="text-gray-900 font-medium">{dateParts.monthDay}</span>
                            </span>
                          );
                        })()}
                      </TableCell>

                      {/* 投手 */}
                      <TableCell className="text-xs truncate max-w-[80px]" title={report.submitter_name}>
                        {report.submitter_name || '-'}
                      </TableCell>

                      {/* 团队 - 响应式隐藏 */}
                      <TableCell className="text-xs truncate max-w-[80px] hidden md:table-cell" title={report.team_name}>
                        {report.team_name || '-'}
                      </TableCell>

                      {/* 地区 - 响应式隐藏 */}
                      <TableCell className="hidden lg:table-cell">
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 font-normal">
                          {getRegionLabel(report.region)}
                        </Badge>
                      </TableCell>

                      {/* 平台 - 响应式隐藏 */}
                      <TableCell className="hidden lg:table-cell">
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 font-normal">
                          {getPlatformLabel(report.platform)}
                        </Badge>
                      </TableCell>

                      {/* 消耗 - 右对齐 + 等宽数字 + 强调色 */}
                      <TableCell className="text-right font-semibold tabular-nums text-xs font-mono text-gray-900">
                        {formatAmount(report.raw_spend, currency)}
                      </TableCell>

                      {/* 进粉数 - 右对齐 + 强调色 */}
                      <TableCell className="text-right tabular-nums text-xs font-mono text-gray-900">
                        {(report.follows_count ?? 0).toLocaleString()}
                      </TableCell>

                      {/* 成效数 - 右对齐 + 强调色 */}
                      <TableCell className="text-right tabular-nums text-xs font-mono text-gray-900">
                        {(report.result_count ?? 0).toLocaleString()}
                      </TableCell>

                      {/* 单粉成本 - 右对齐 + 响应式隐藏 */}
                      <TableCell className="text-right tabular-nums text-xs font-mono text-muted-foreground hidden sm:table-cell">
                        {report.cost_per_follow
                          ? formatAmount(report.cost_per_follow, currency)
                          : formatCostMetric(report.raw_spend, report.follows_count ?? 0, currency)}
                      </TableCell>

                      {/* 成效费用 - 右对齐 + 响应式隐藏 */}
                      <TableCell className="text-right tabular-nums text-xs font-mono text-muted-foreground hidden sm:table-cell">
                        {report.cost_per_result
                          ? formatAmount(report.cost_per_result, currency)
                          : formatCostMetric(report.raw_spend, report.result_count ?? 0, currency)}
                      </TableCell>

                      {/* 状态 - v3.0 带色点 Badge */}
                      <TableCell>
                        {(() => {
                          const visual = STATUS_VISUAL[report.status] || STATUS_VISUAL.raw_submitted;
                          return (
                            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium ${visual.bg} ${visual.text}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${visual.dot}`} />
                              {statusConfig.label}
                            </span>
                          );
                        })()}
                      </TableCell>

                      {/* 操作 */}
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-7 w-7">
                              <MoreHorizontal className="h-3.5 w-3.5" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-36">
                            {report.status === 'raw_submitted' && (
                              <DropdownMenuItem
                                onClick={() => submitTrendMutation.mutate(String(report.id))}
                                disabled={submitTrendMutation.isPending}
                                className="text-xs"
                              >
                                <Send className="mr-2 h-3.5 w-3.5" />
                                提交趋势审核
                              </DropdownMenuItem>
                            )}
                            {report.status === 'trend_pending' && (
                              <DropdownMenuItem
                                onClick={() => approveTrendMutation.mutate(String(report.id))}
                                disabled={approveTrendMutation.isPending}
                                className="text-xs"
                              >
                                <Check className="mr-2 h-3.5 w-3.5" />
                                趋势通过
                              </DropdownMenuItem>
                            )}
                            {(report.status === 'trend_ok' || report.status === 'trend_resolved') && (
                              <DropdownMenuItem
                                onClick={() => submitFinalMutation.mutate(String(report.id))}
                                disabled={submitFinalMutation.isPending}
                                className="text-xs"
                              >
                                <Send className="mr-2 h-3.5 w-3.5" />
                                提交终审
                              </DropdownMenuItem>
                            )}
                            {report.status === 'final_confirmed' && (
                              <DropdownMenuItem
                                onClick={() => lockMutation.mutate(String(report.id))}
                                disabled={lockMutation.isPending}
                                className="text-xs"
                              >
                                <Lock className="mr-2 h-3.5 w-3.5" />
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
          </div>
        </div>

        {/* 分页 */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-between px-1">
            <div className="text-xs text-muted-foreground">
              共 {pagination.total.toLocaleString()} 条 · 第 {pagination.page}/{pagination.total_pages} 页
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                上一页
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= pagination.total_pages}
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
});

// 设置 displayName 以便调试
DailyReportsTable.displayName = 'DailyReportsTable';
