/**
 * AdAccountsTableV2 Component
 *
 * 账户表格 - 高信息密度设计
 * 从 AdAccountsPageV2.tsx 提取
 * 使用 ScrollArea 优化滚动体验
 */

'use client';

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  MoreHorizontal,
  Copy,
  Eye,
  Pause,
  Play,
  Archive,
  Users,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  formatCurrency,
  formatPercent,
  getStatusConfig,
  getPlatformConfig,
  type AdAccountV2Display,
} from '../utils/adAccountsHelpers';

export interface AdAccountsTableV2Props {
  accounts: AdAccountV2Display[];
  selectedIds: Set<number>;
  onSelectChange: (id: number, checked: boolean) => void;
  onSelectAll: (checked: boolean) => void;
  onViewDetail?: (account: AdAccountV2Display) => void;
  onOpenInPlatform?: (account: AdAccountV2Display) => void;
  onPauseAccount?: (account: AdAccountV2Display) => void;
  onResumeAccount?: (account: AdAccountV2Display) => void;
  onReassignAccount?: (account: AdAccountV2Display) => void;
  onMarkAsDead?: (account: AdAccountV2Display) => void;
  pageSize?: number;
  onPageSizeChange?: (size: number) => void;
  className?: string;
}

export function AdAccountsTableV2({
  accounts,
  selectedIds,
  onSelectChange,
  onSelectAll,
  onViewDetail,
  onOpenInPlatform,
  onPauseAccount,
  onResumeAccount,
  onReassignAccount,
  onMarkAsDead,
  pageSize = 20,
  onPageSizeChange,
  className,
}: AdAccountsTableV2Props) {
  const allSelected = accounts.length > 0 && accounts.every(a => selectedIds.has(a.id));

  const handleCopyId = (platformId: string) => {
    navigator.clipboard.writeText(platformId);
  };

  return (
    <div className={cn('border rounded-lg overflow-hidden bg-white', className)} data-testid="ad-accounts-table">
      <ScrollArea className="w-full">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50/80">
              <TableHead className="w-[40px]">
                <Checkbox
                  checked={allSelected}
                  onCheckedChange={(checked) => onSelectAll(!!checked)}
                  aria-label="全选"
                />
              </TableHead>
              <TableHead className="min-w-[280px]">账户信息</TableHead>
              <TableHead className="w-[80px]">投手</TableHead>
              <TableHead className="w-[160px]">代理商</TableHead>
              <TableHead className="w-[100px] text-right">今日消耗</TableHead>
              <TableHead className="w-[100px] text-right">本月消耗</TableHead>
              <TableHead className="w-[80px] text-center">状态</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account) => {
              const statusConfig = getStatusConfig(account.status);
              const platformConfig = getPlatformConfig(account.platform);

              return (
                <TableRow
                  key={account.id}
                  className={cn(
                    'group hover:bg-blue-50/50 transition-colors',
                    selectedIds.has(account.id) && 'bg-blue-50'
                  )}
                >
                  <TableCell>
                    <Checkbox
                      checked={selectedIds.has(account.id)}
                      onCheckedChange={(checked) => onSelectChange(account.id, !!checked)}
                    />
                  </TableCell>

                  {/* 账户信息 - 紧凑但完整 */}
                  <TableCell>
                    <div className="flex items-start gap-3">
                      {/* 平台标识 */}
                      <div className={cn(
                        'w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0',
                        platformConfig.color
                      )}>
                        {account.platform}
                      </div>

                      <div className="min-w-0 flex-1">
                        {/* 账户名称 */}
                        <div className="flex items-center gap-2">
                          <span
                            className="font-medium text-gray-900 truncate hover:text-blue-600 cursor-pointer"
                            onClick={() => onViewDetail?.(account)}
                          >
                            {account.name}
                          </span>
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span
                                  role="button"
                                  tabIndex={0}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                                  onClick={() => handleCopyId(account.platformId)}
                                  onKeyDown={(e) => e.key === 'Enter' && handleCopyId(account.platformId)}
                                >
                                  <Copy className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>复制账户ID</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>

                        {/* 次要信息 */}
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-gray-400 font-mono">
                            {account.platformId}
                          </span>
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                            {account.accountType}
                          </Badge>
                          <span className="text-xs text-gray-400">{account.region}</span>
                        </div>
                      </div>
                    </div>
                  </TableCell>

                  {/* 投手 */}
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-xs font-medium">
                        {account.buyer.charAt(0)}
                      </div>
                      <span className="text-sm font-medium">{account.buyer}</span>
                    </div>
                  </TableCell>

                  {/* 代理商 */}
                  <TableCell>
                    <span className="text-sm text-gray-600 truncate block max-w-[140px]" title={account.supplier}>
                      {account.supplier}
                    </span>
                    <span className="text-xs text-gray-400">费率 {(account.feeRate * 100).toFixed(0)}%</span>
                  </TableCell>

                  {/* 今日消耗 - 带趋势 */}
                  <TableCell className="text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-medium tabular-nums">
                        {formatCurrency(account.todaySpend)}
                      </span>
                      <div className={cn(
                        'flex items-center gap-0.5 text-xs',
                        account.trend > 0 ? 'text-green-600' : account.trend < 0 ? 'text-red-500' : 'text-gray-400'
                      )}>
                        {account.trend > 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : account.trend < 0 ? (
                          <TrendingDown className="w-3 h-3" />
                        ) : null}
                        <span>{formatPercent(account.trend)}</span>
                      </div>
                    </div>
                  </TableCell>

                  {/* 本月消耗 */}
                  <TableCell className="text-right">
                    <span className="font-medium tabular-nums">
                      {formatCurrency(account.monthSpend)}
                    </span>
                  </TableCell>

                  {/* 状态 */}
                  <TableCell className="text-center">
                    <Badge
                      variant="secondary"
                      className={cn(
                        'text-xs',
                        statusConfig.bgColor,
                        statusConfig.textColor
                      )}
                    >
                      <span className={cn('w-1.5 h-1.5 rounded-full mr-1.5', statusConfig.color)} />
                      {statusConfig.label}
                    </Badge>
                  </TableCell>

                  {/* 操作 */}
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onViewDetail?.(account)}>
                          <Eye className="w-4 h-4 mr-2" />
                          查看详情
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => onOpenInPlatform?.(account)}>
                          <ExternalLink className="w-4 h-4 mr-2" />
                          在平台中打开
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {account.status === 'active' ? (
                          <DropdownMenuItem onClick={() => onPauseAccount?.(account)}>
                            <Pause className="w-4 h-4 mr-2" />
                            暂停投放
                          </DropdownMenuItem>
                        ) : account.status === 'suspended' ? (
                          <DropdownMenuItem onClick={() => onResumeAccount?.(account)}>
                            <Play className="w-4 h-4 mr-2" />
                            恢复投放
                          </DropdownMenuItem>
                        ) : null}
                        <DropdownMenuItem onClick={() => onReassignAccount?.(account)}>
                          <Users className="w-4 h-4 mr-2" />
                          重新分配
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={() => onMarkAsDead?.(account)}
                        >
                          <Archive className="w-4 h-4 mr-2" />
                          标记死号
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>

      {/* 表格底部 */}
      <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50/50">
        <span className="text-sm text-gray-500">
          共 {accounts.length} 个账户
        </span>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">每页</span>
          <Select
            value={String(pageSize)}
            onValueChange={(v) => onPageSizeChange?.(Number(v))}
          >
            <SelectTrigger className="w-[70px] h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
              <SelectItem value="100">100</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-gray-500">条</span>
        </div>
      </div>
    </div>
  );
}

export default AdAccountsTableV2;
