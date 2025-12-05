/**
 * FinancePageShell - 财务管理模块 Shell 组件
 *
 * 布局结构：
 * - Header: 标题 + 操作按钮
 * - Tabs: 财务概览 / 充值管理 / 财务分析 / 团队预算
 * - 主内容区: 根据 Tab 切换显示
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

'use client';

import React from 'react';
import { DollarSign, Plus, Download } from 'lucide-react';
import { Loader2 } from 'lucide-react';
import { PageShell } from '@/modules/shared';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useFinanceFilters, useFinanceData } from '../hooks';
import { FinanceKpiRow } from './FinanceKpiRow';
import { FinanceTopupTable } from './FinanceTopupTable';
import {
  SpendingTrendChart,
  PlatformPieChart,
  PlatformBarChart,
  MonthlyComparison,
  BudgetProjection,
  TeamBudgetList,
} from './FinanceCharts';

export interface FinancePageShellProps {
  className?: string;
}

export function FinancePageShell({ className }: FinancePageShellProps) {
  // 筛选状态
  const { filters, setSearch, setStatus, setActiveTab } = useFinanceFilters();

  // 数据获取
  const {
    data,
    filteredTopupRequests,
    pendingCount,
    loading,
    error,
    refresh,
    approveRequest,
    rejectRequest,
    completeRequest,
  } = useFinanceData(filters);

  // 加载状态
  if (loading && !data.topupRequests.length) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-text-muted">
        <Loader2 className="w-8 h-8 animate-spin mr-2" />
        加载财务管理数据中...
      </div>
    );
  }

  // 错误状态
  if (error && !data.topupRequests.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-text-muted">
        <p className="text-danger mb-4">{error.message}</p>
        <Button
          onClick={refresh}
          className="bg-accent text-white hover:bg-accent/90"
        >
          重新加载
        </Button>
      </div>
    );
  }

  return (
    <PageShell
      title="财务管理"
      description="充值审批、预算控制、财务分析"
      icon={DollarSign}
      className={className}
      actions={
        <>
          <Button variant="outline" className="bg-card border-border gap-2">
            <Download className="w-4 h-4" />
            导出报表
          </Button>
          <Button className="bg-accent hover:bg-accent/90 gap-2">
            <Plus className="w-4 h-4" />
            充值申请
          </Button>
        </>
      }
    >
      <Tabs
        value={filters.activeTab}
        onValueChange={(v) =>
          setActiveTab(v as typeof filters.activeTab)
        }
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-4 bg-card border border-border">
          <TabsTrigger
            value="overview"
            className="data-[state=active]:bg-accent data-[state=active]:text-white"
          >
            财务概览
          </TabsTrigger>
          <TabsTrigger
            value="topup"
            className="data-[state=active]:bg-accent data-[state=active]:text-white"
          >
            充值管理
          </TabsTrigger>
          <TabsTrigger
            value="analysis"
            className="data-[state=active]:bg-accent data-[state=active]:text-white"
          >
            财务分析
          </TabsTrigger>
          <TabsTrigger
            value="team"
            className="data-[state=active]:bg-accent data-[state=active]:text-white"
          >
            团队预算
          </TabsTrigger>
        </TabsList>

        {/* 财务概览 Tab */}
        <TabsContent value="overview" className="space-y-6">
          <FinanceKpiRow
            summary={data.financialSummary}
            pendingCount={pendingCount}
            loading={loading}
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SpendingTrendChart data={data.spendingTrends} />
            <PlatformPieChart data={data.platformSpending} />
          </div>
        </TabsContent>

        {/* 充值管理 Tab */}
        <TabsContent value="topup" className="space-y-6">
          <FinanceTopupTable
            requests={filteredTopupRequests}
            searchTerm={filters.search}
            statusFilter={filters.status}
            onSearchChange={setSearch}
            onStatusChange={setStatus}
            onApprove={approveRequest}
            onReject={rejectRequest}
            onComplete={completeRequest}
          />
        </TabsContent>

        {/* 财务分析 Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MonthlyComparison summary={data.financialSummary} />
            <BudgetProjection summary={data.financialSummary} />
            <PlatformBarChart data={data.platformSpending} />
          </div>
        </TabsContent>

        {/* 团队预算 Tab */}
        <TabsContent value="team" className="space-y-6">
          <TeamBudgetList data={data.teamSpending} />
        </TabsContent>
      </Tabs>
    </PageShell>
  );
}

export default FinancePageShell;
