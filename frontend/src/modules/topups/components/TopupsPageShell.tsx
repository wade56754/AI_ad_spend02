/**
 * TopupsPageShell - 充值管理页面主容器
 *
 * 布局结构：
 * - Header: 标题 + 状态筛选 + 新建充值
 * - KPI 区: 充值统计
 * - 主内容: 充值列表表格
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, TOPUP_SOT.md
 */

'use client';

import React from 'react';
import { DollarSign, Plus, Search, Filter } from 'lucide-react';
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
import { TopupsKpiRow } from './TopupsKpiRow';
import { TopupsDataTable } from './TopupsDataTable';
import { useTopups } from '../hooks';
import type { TopupStatus, TopupFilters } from '../types';

export function TopupsPageShell() {
  const [filters, setFilters] = React.useState<TopupFilters>({});

  const { data: topupsData, isLoading } = useTopups(filters);

  const topups = topupsData?.data ?? [];
  const loading = isLoading;

  const summary = {
    total: topups.length,
    pending: topups.filter(t => t.status === 'pending').length,
    approved: topups.filter(t => t.status === 'approved').length,
    completed: topups.filter(t => t.status === 'completed').length,
    total_amount: topups.reduce((sum, t) => sum + t.amount, 0),
  };

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      const { status, ...rest } = filters;
      setFilters(rest);
    } else {
      setFilters({ ...filters, status: value as TopupStatus });
    }
  };

  return (
    <PageShell
      title="充值管理"
      description="管理账户充值请求，审批流程和充值记录"
      icon={DollarSign}
      filters={
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input
              placeholder="搜索充值..."
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
              <SelectItem value="pending" className="text-text-body hover:bg-elevated">待审批</SelectItem>
              <SelectItem value="approved" className="text-text-body hover:bg-elevated">已审批</SelectItem>
              <SelectItem value="completed" className="text-text-body hover:bg-elevated">已完成</SelectItem>
              <SelectItem value="rejected" className="text-text-body hover:bg-elevated">已拒绝</SelectItem>
            </SelectContent>
          </Select>
        </>
      }
      actions={
        <Button
          size="sm"
          className="gap-2 bg-success hover:bg-success-emphasis shadow-lg shadow-success/20"
        >
          <Plus className="w-4 h-4" />
          申请充值
        </Button>
      }
      kpiSection={<TopupsKpiRow summary={summary} loading={loading} />}
    >
      <TopupsDataTable
        topups={topups}
        loading={loading}
        onRowClick={(topup) => console.log('View topup:', topup)}
      />
    </PageShell>
  );
}

export default TopupsPageShell;
