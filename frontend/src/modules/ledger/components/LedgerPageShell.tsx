/**
 * LedgerPageShell - 账本查询页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 账户筛选 + 类型筛选 + 日期范围
 * - KPI 区: 余额、收入、支出统计
 * - 主内容: 账本流水表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, LEDGER_SOT.md v1.1
 */

'use client';

import React from 'react';
import { BookOpen, Search, Calendar, Filter } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { LedgerKpiRow } from './LedgerKpiRow';
import { LedgerDataTable } from './LedgerDataTable';
import { useLedgerEntries } from '../hooks';
import type { LedgerEntryType, LedgerFilters, LedgerListParams } from '../types';

export function LedgerPageShell() {
  const [filters, setFilters] = React.useState<LedgerFilters>({});

  // Convert LedgerFilters to LedgerListParams for the hook
  const queryParams: LedgerListParams = {
    entry_type: filters.entry_type,
    // search filter handled client-side if needed
  };

  const { data: ledgerData, isLoading } = useLedgerEntries(queryParams);

  const entries = ledgerData?.data ?? [];
  const loading = isLoading;

  const summary = {
    total_entries: entries.length,
    total_credit: entries
      .filter(e => e.amount > 0)
      .reduce((sum, e) => sum + e.amount, 0),
    total_debit: entries
      .filter(e => e.amount < 0)
      .reduce((sum, e) => sum + Math.abs(e.amount), 0),
    balance: entries.reduce((sum, e) => sum + e.amount, 0),
  };

  const handleTypeChange = (value: string) => {
    if (value === 'all') {
      const { entry_type, ...rest } = filters;
      setFilters(rest);
    } else {
      setFilters({ ...filters, entry_type: value as LedgerEntryType });
    }
  };

  return (
    <PageShell
      title="账本查询"
      description="查询账本流水，包括充值、消费、调整等所有账目记录"
      icon={BookOpen}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索流水..."
              className="pl-9 w-[200px] bg-card-bg border-border-default text-text-body placeholder:text-text-muted"
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <Select onValueChange={handleTypeChange} defaultValue="all">
            <SelectTrigger className="w-[120px] bg-card-bg border-border-default text-text-body">
              <SelectValue placeholder="类型" />
            </SelectTrigger>
            <SelectContent className="bg-card-bg border-border-default">
              <SelectItem value="all" className="text-text-body hover:bg-elevated">全部类型</SelectItem>
              <SelectItem value="RECHARGE" className="text-text-body hover:bg-elevated">充值</SelectItem>
              <SelectItem value="SPEND" className="text-text-body hover:bg-elevated">消费</SelectItem>
              <SelectItem value="ADJUSTMENT" className="text-text-body hover:bg-elevated">调整</SelectItem>
              <SelectItem value="TRANSFER" className="text-text-body hover:bg-elevated">转移</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated"
          >
            <Calendar className="w-4 h-4" />
            日期范围
          </Button>
        </>
      }
      actions={
        <Button
          variant="outline"
          size="sm"
          className="gap-2 bg-card-bg border-border-default text-text-body hover:bg-elevated"
        >
          <Filter className="w-4 h-4" />
          高级筛选
        </Button>
      }
      kpiSection={<LedgerKpiRow summary={summary} loading={loading} />}
    >
      <LedgerDataTable
        entries={entries}
        loading={loading}
        onRowClick={(entry) => console.log('View entry:', entry)}
      />
    </PageShell>
  );
}

export default LedgerPageShell;
