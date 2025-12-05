/**
 * ReconciliationPageShell - 对账管理页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 状态筛选 + 日期范围
 * - KPI 区: 对账批次统计
 * - 主内容: 对账批次表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3
 */

'use client';

import React from 'react';
import { CheckSquare, Plus, Search, Calendar } from 'lucide-react';
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
import { ReconciliationKpiRow } from './ReconciliationKpiRow';
import { ReconciliationDataTable } from './ReconciliationDataTable';
import { useReconciliation } from '../hooks';
import type { ReconciliationStatus, ReconciliationFilters } from '../types';

export function ReconciliationPageShell() {
  const [filters, setFilters] = React.useState<ReconciliationFilters>({});

  const { data: reconciliationData, isLoading } = useReconciliation(filters);

  const batches = reconciliationData?.data ?? [];
  const loading = isLoading;

  const summary = {
    total: batches.length,
    pending: batches.filter(b => b.status === 'pending').length,
    matched: batches.filter(b => b.status === 'matched').length,
    has_diff: batches.filter(b => b.status === 'has_diff').length,
    resolved: batches.filter(b => b.status === 'resolved').length,
  };

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      const { status, ...rest } = filters;
      setFilters(rest);
    } else {
      setFilters({ ...filters, status: value as ReconciliationStatus });
    }
  };

  return (
    <PageShell
      title="对账管理"
      description="管理账户对账批次，处理差异调整和对账确认"
      icon={CheckSquare}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索批次..."
              className="pl-9 w-[200px] bg-card-bg border-border-default text-text-body placeholder:text-text-muted"
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <Select onValueChange={handleStatusChange} defaultValue="all">
            <SelectTrigger className="w-[120px] bg-card-bg border-border-default text-text-body">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent className="bg-card-bg border-border-default">
              <SelectItem value="all" className="text-text-body hover:bg-elevated">全部状态</SelectItem>
              <SelectItem value="pending" className="text-text-body hover:bg-elevated">待对账</SelectItem>
              <SelectItem value="matched" className="text-text-body hover:bg-elevated">已匹配</SelectItem>
              <SelectItem value="has_diff" className="text-text-body hover:bg-elevated">有差异</SelectItem>
              <SelectItem value="resolved" className="text-text-body hover:bg-elevated">已解决</SelectItem>
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
          size="sm"
          className="gap-2 bg-accent hover:bg-accent-hover shadow-lg shadow-accent/20"
        >
          <Plus className="w-4 h-4" />
          创建批次
        </Button>
      }
      kpiSection={<ReconciliationKpiRow summary={summary} loading={loading} />}
    >
      <ReconciliationDataTable
        batches={batches}
        loading={loading}
        onRowClick={(batch) => console.log('View batch:', batch)}
      />
    </PageShell>
  );
}

export default ReconciliationPageShell;
