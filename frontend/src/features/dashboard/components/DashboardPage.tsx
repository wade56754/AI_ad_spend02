/**
 * DashboardPage Component
 *
 * SoT: docs/10.module-specs/A1-dashboard.md
 * SoT: MASTER.md v4.4 §6.5 核心页面最小字段集
 *
 * 布局: PageHeader → StatCards → TrendCharts → TopLists → PendingTasks → BottomSection
 * 间距: gap-6 (24px) 卡片网格, gap-8 (32px) 分区
 * 排版: H2 = text-2xl font-semibold
 */

'use client';

import React, { useState, useMemo, useCallback } from 'react';
import Link from 'next/link';
import {
  DollarSign,
  Users,
  BarChart3,
  Target,
  Plus,
  FileText,
  Wallet,
  Activity,
  AlertTriangle,
  CreditCard,
} from 'lucide-react';
import { useAuth } from '@/features/auth';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Alert as AlertUI, AlertDescription } from '@/components/ui/alert';

import { DashboardHeader } from './DashboardHeader';
import { StatCard } from './StatCard';
import { StatusCard } from './StatusCard';
import { PendingTasksCard } from './PendingTasksCard';
import { AccountOverviewCard } from './AccountOverviewCard';
import { SystemStatusCard } from './SystemStatusCard';
import {
  StatCardSkeleton,
  TrendChartSkeleton,
  CardSkeleton,
} from './StatCardSkeleton';
import {
  GlobalDateFilter,
  type DateRangePreset,
  getDateRangeFromPreset,
} from './GlobalDateFilter';
import { AlertBanner, generateAlertsFromData, type Alert } from './AlertBanner';
import {
  MainTrendChart,
  type MetricType,
  type TrendDataPoint as MainTrendDataPoint,
  generateSummary,
} from './MainTrendChart';

import { useDashboardData, useRefreshDashboard, showAlertToasts, showSuccessToast } from '../hooks';
import { formatCurrency, formatCurrencyWan } from '../utils/formatters';
import { safeAverage } from '@/lib';
import type { PendingTask } from '../types';

export function DashboardPage() {
  const { user, isLoading: isAuthLoading } = useAuth();

  // ============ 状态管理 ============

  // 全局日期范围状态
  const [globalDateRange, setGlobalDateRange] = useState<DateRangePreset>('7d');

  // 选中的指标状态 (用于 KPI 卡片联动主图)
  const [activeMetric, setActiveMetric] = useState<MetricType>('spend');

  // 告警列表 - 初始为空，避免 hydration 错误
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // ============ 数据获取 (TanStack Query) ============
  // SoT: A1-dashboard.md §2.4 数据刷新策略

  // 使用统一的日期范围工具函数，转换 Date 为 API 需要的字符串格式
  const dateRange = useMemo(() => {
    const range = getDateRangeFromPreset(globalDateRange);
    return {
      from: range.from.toISOString().split('T')[0],
      to: range.to.toISOString().split('T')[0],
    };
  }, [globalDateRange]);

  const {
    overview,
    trend,
    topProjects,
    pendingCounts,
    isLoading: isDataLoading,
    isError,
    error,
    queries,
  } = useDashboardData(dateRange);

  const { refreshAll } = useRefreshDashboard();

  // 检查是否有任何查询正在刷新 (非初次加载)
  const isRefreshing =
    (queries.overview.isFetching && !queries.overview.isLoading) ||
    (queries.trend.isFetching && !queries.trend.isLoading) ||
    (queries.topProjects.isFetching && !queries.topProjects.isLoading) ||
    (queries.pendingCounts.isFetching && !queries.pendingCounts.isLoading);

  // 根据实际数据生成告警
  React.useEffect(() => {
    if (isDataLoading) return;

    // 计算 7 日均值消耗
    const last7Days = (trend?.points ?? []).slice(-7);
    const avgSpend = last7Days.length > 0
      ? last7Days.reduce((sum, d) => sum + (d.spend || 0), 0) / last7Days.length
      : 0;

    // 计算待处理总数
    const totalPending =
      (pendingCounts?.pending_topups ?? 0) +
      (pendingCounts?.pending_settlements ?? 0) +
      (pendingCounts?.pending_reconciliations ?? 0) +
      (pendingCounts?.pending_imports ?? 0);

    const realAlerts = generateAlertsFromData({
      abnormal_projects: overview?.abnormal_projects ?? 0,
      pending_topups: pendingCounts?.pending_topups ?? 0,
      today_spend: overview?.today_spend ?? 0,
      average_spend: avgSpend,
      total_pending: totalPending,
    });

    setAlerts(realAlerts);

    // 同时用 toast 显示高优先级告警 (critical/warning)
    showAlertToasts(realAlerts.filter(a => a.severity !== 'info'));
  }, [isDataLoading, overview, trend, pendingCounts]);

  // ============ 派生数据 ============
  // SoT: MASTER.md §6.5 核心页面最小字段集

  // 从 API 响应构建统计数据，提供默认值
  const stats = useMemo(() => ({
    // §6.5 必须字段 - 本月核心指标
    month_spend: overview?.total_spend ?? 0,
    month_conversions: overview?.total_conversions ?? 0,
    overall_cpl: overview?.cpl ?? 0,
    estimated_profit: overview?.total_profit ?? 0,
    active_projects: overview?.active_projects ?? 0,
    abnormal_projects: overview?.abnormal_projects ?? 0,
    pending_topups: pendingCounts?.pending_topups ?? 0,
    // 今日视角 (扩展字段)
    today_spend: overview?.today_spend ?? 0,
    today_conversions: overview?.today_conversions ?? 0,
    today_revenue: overview?.today_revenue ?? 0,
    today_profit: overview?.today_profit ?? 0,
    // 变化率
    spend_change: overview?.spend_change ?? 0,
    conversions_change: overview?.conversions_change ?? 0,
    cpl_change: overview?.cpl ? -((overview.cpl - (overview.cpl_target ?? 35)) / (overview.cpl_target ?? 35) * 100) : 0,
    profit_change: overview?.profit_change ?? 0,
    // 其他待处理
    pending_settlements: pendingCounts?.pending_settlements ?? 0,
    pending_reconciliations: pendingCounts?.pending_reconciliations ?? 0,
    pending_imports: pendingCounts?.pending_imports ?? 0,
    active_accounts: 45, // TODO: 需要后端 API 支持
    total_balance: 856000.00, // TODO: 需要后端 API 支持
    // CPL 目标
    cpl_target: overview?.cpl_target ?? 35.00,
  }), [overview, pendingCounts]);

  // 转换趋势数据格式
  const mainTrendData: MainTrendDataPoint[] = useMemo(
    () => trend?.points ?? [],
    [trend]
  );

  // 生成自动总结
  const trendSummary = useMemo(
    () => generateSummary(mainTrendData, activeMetric),
    [mainTrendData, activeMetric]
  );

  // 计算 7 日均值 (用于 KPI 卡片)
  // FE-P0-1 修复: 使用 safeAverage 替代硬编码除以 7，正确处理不足 7 天的情况
  const average7d = useMemo(() => {
    const last7Days = mainTrendData.slice(-7);
    // safeAverage 会正确除以实际数组长度，而非固定值 7
    const avgSpend = safeAverage(last7Days.map(d => d.spend));
    const avgRevenue = safeAverage(last7Days.map(d => d.revenue));
    const avgProfit = safeAverage(last7Days.map(d => d.profit));
    const avgConversions = safeAverage(last7Days.map(d => d.conversions));

    return {
      spend: formatCurrency(avgSpend),
      revenue: formatCurrency(avgRevenue),
      profit: formatCurrency(avgProfit),
      conversions: Math.round(avgConversions).toLocaleString(),
    };
  }, [mainTrendData]);


  // Pending tasks data
  const pendingTasks: PendingTask[] = [
    {
      id: 'topups',
      title: '待审批充值',
      count: stats.pending_topups,
      href: '/topups?status=pending',
      priority: 'high',
      icon: 'credit-card',
    },
    {
      id: 'settlements',
      title: '待结算项目',
      count: stats.pending_settlements,
      href: '/settlements?status=pending',
      priority: 'medium',
      icon: 'wallet',
    },
    {
      id: 'reconciliations',
      title: '待对账记录',
      count: stats.pending_reconciliations,
      href: '/reconciliation?status=pending',
      priority: 'medium',
      icon: 'check-circle',
    },
    {
      id: 'imports',
      title: '待处理导入',
      count: stats.pending_imports,
      href: '/import-jobs?status=pending',
      priority: 'low',
      icon: 'file-text',
    },
  ];

  /**
   * 刷新所有驾驶舱数据
   * SoT: A1-dashboard.md §2.4 数据刷新策略
   */
  const handleRefresh = useCallback(async () => {
    await refreshAll();
    showSuccessToast('数据刷新成功');
  }, [refreshAll]);

  // 稳定的指标切换回调 (避免子组件不必要的重渲染)
  const handleMetricChange = useCallback((metric: MetricType) => {
    setActiveMetric(metric);
  }, []);

  // 各指标的独立回调 (用于 StatCard onClick)
  const handleSpendClick = useCallback(() => setActiveMetric('spend'), []);
  const handleConversionsClick = useCallback(() => setActiveMetric('conversions'), []);
  const handleProfitClick = useCallback(() => setActiveMetric('profit'), []);

  // 稳定的日期范围切换回调
  const handleDateRangeChange = useCallback((preset: DateRangePreset) => {
    setGlobalDateRange(preset);
  }, []);

  // 稳定的告警关闭回调
  const handleDismissAlert = useCallback((id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  // Show skeleton loading state while auth or data is initializing
  if (isAuthLoading || isDataLoading) {
    return (
      <div className="space-y-8" data-testid="loading-skeleton">
        {/* Header Skeleton */}
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="w-48 h-9 rounded mb-2" />
            <Skeleton className="w-64 h-5 rounded" />
          </div>
          <Skeleton className="w-20 h-10 rounded" />
        </div>

        {/* Stat Cards Skeleton */}
        <section>
          <Skeleton className="w-24 h-7 rounded mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>
        </section>

        {/* Trend Charts Skeleton */}
        <section>
          <Skeleton className="w-24 h-7 rounded mb-4" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <TrendChartSkeleton />
            <TrendChartSkeleton />
          </div>
          <TrendChartSkeleton />
        </section>

        {/* Bottom Section Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <CardSkeleton />
            <CardSkeleton />
          </div>
          <div className="space-y-6">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );
  }

  // 显示错误状态
  if (isError) {
    return (
      <div className="space-y-6" data-testid="error-state">
        <AlertUI variant="destructive">
          <AlertDescription>
            加载驾驶舱数据失败: {error?.message || '未知错误'}
            <Button variant="outline" size="sm" className="ml-4" onClick={handleRefresh} data-testid="retry-button">
              重试
            </Button>
          </AlertDescription>
        </AlertUI>
      </div>
    );
  }

  // 检查是否为空数据状态 (所有核心指标都为 0 或 null)
  const isEmptyData =
    stats.month_spend === 0 &&
    stats.month_conversions === 0 &&
    stats.active_projects === 0 &&
    mainTrendData.length === 0;

  if (isEmptyData) {
    return (
      <div className="space-y-6" data-testid="empty-state">
        <DashboardHeader
          userName={user?.full_name || user?.username || '用户'}
          isRefreshing={isRefreshing}
          onRefresh={handleRefresh}
        />
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-6 mb-4">
            <BarChart3 className="h-12 w-12 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">暂无数据</h2>
          <p className="text-muted-foreground mb-6">
            当前筛选条件下没有数据，请尝试调整时间范围或创建新项目
          </p>
          <div className="flex gap-3">
            <Link href="/projects/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                创建新推广计划
              </Button>
            </Link>
            <Button variant="outline" onClick={handleRefresh}>
              刷新数据
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Page Header with Global Date Filter */}
      <div className="flex items-center justify-between">
        <DashboardHeader
          userName={user?.full_name || user?.username || '用户'}
          isRefreshing={isRefreshing}
          onRefresh={handleRefresh}
        />
        <GlobalDateFilter
          value={globalDateRange}
          onChange={handleDateRangeChange}
        />
      </div>

      {/* Alert Banner - 风险告警条 */}
      {alerts.length > 0 && (
        <AlertBanner
          alerts={alerts}
          onDismiss={handleDismissAlert}
        />
      )}

      {/* Quick Actions - 快捷操作 */}
      <div className="flex gap-3">
        <Link href="/projects/new">
          <Button className="shadow-sm">
            <Plus className="h-4 w-4 mr-2" />
            创建新推广计划
          </Button>
        </Link>
        <Link href="/reports">
          <Button variant="outline" className="shadow-sm">
            <FileText className="h-4 w-4 mr-2" />
            查看报表
          </Button>
        </Link>
        <Link href="/finance">
          <Button variant="outline" className="shadow-sm">
            <Wallet className="h-4 w-4 mr-2" />
            财务中心
          </Button>
        </Link>
      </div>

      {/* SECTION A: 本月概览 (MASTER.md §6.5 必须字段) */}
      <section data-testid="kpi-cards">
        <h2 className="text-2xl font-semibold text-foreground mb-4">本月概览</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="本月总消耗"
            value={formatCurrency(stats.month_spend)}
            change={stats.spend_change}
            average7d={average7d.spend}
            target={`今日 ${formatCurrency(stats.today_spend)}`}
            icon={<DollarSign className="h-6 w-6" />}
            color="blue"
            onClick={handleSpendClick}
            isActive={activeMetric === 'spend'}
            testId="kpi-spend"
          />
          <StatCard
            title="本月总进粉"
            value={stats.month_conversions.toLocaleString()}
            change={stats.conversions_change}
            average7d={average7d.conversions}
            target={`今日 ${stats.today_conversions.toLocaleString()}`}
            icon={<Users className="h-6 w-6" />}
            color="purple"
            onClick={handleConversionsClick}
            isActive={activeMetric === 'conversions'}
            testId="kpi-conversions"
          />
          <StatCard
            title="整体 CPL"
            value={`¥${stats.overall_cpl.toFixed(2)}`}
            change={stats.cpl_change}
            target={`目标 ¥${stats.cpl_target}`}
            icon={<BarChart3 className="h-6 w-6" />}
            color={stats.overall_cpl > stats.cpl_target * 1.3 ? 'red' : stats.overall_cpl > stats.cpl_target ? 'orange' : 'green'}
            testId="kpi-cpl"
          />
          <StatCard
            title="预计毛利"
            value={formatCurrency(stats.estimated_profit)}
            change={stats.profit_change}
            average7d={average7d.profit}
            target={`今日 ${formatCurrency(stats.today_profit)}`}
            icon={<Target className="h-6 w-6" />}
            color={stats.estimated_profit >= 0 ? 'green' : 'red'}
            onClick={handleProfitClick}
            isActive={activeMetric === 'profit'}
            testId="kpi-profit"
          />
        </div>
      </section>

      {/* SECTION B: 运营状态 (DASHBOARD_LAYOUT_SPEC.md §2.1) */}
      <section data-testid="ops-status">
        <h2 className="text-2xl font-semibold text-foreground mb-4">运营状态</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatusCard
            title="活跃项目"
            count={stats.active_projects}
            status="normal"
            icon={<Activity className="h-5 w-5" />}
            actionLabel="查看全部"
            href="/projects?status=active"
            testId="active-projects"
          />
          <StatusCard
            title="异常项目"
            count={stats.abnormal_projects}
            status={stats.abnormal_projects > 0 ? 'critical' : 'normal'}
            description="CPL 超标 30%+"
            icon={<AlertTriangle className="h-5 w-5" />}
            actionLabel="立即处理"
            href="/projects?filter=abnormal"
            testId="abnormal-projects"
          />
          <StatusCard
            title="待审批充值"
            count={stats.pending_topups}
            status={stats.pending_topups > 0 ? 'warning' : 'normal'}
            description="需老板审批"
            icon={<CreditCard className="h-5 w-5" />}
            actionLabel="去审批"
            href="/topups?status=pending"
            testId="pending-topups"
          />
        </div>
      </section>

      {/* SECTION C: 趋势分析 */}
      <MainTrendChart
        data={mainTrendData}
        activeMetric={activeMetric}
        onMetricChange={handleMetricChange}
        summary={trendSummary}
      />


      {/* SECTION E: 待处理事项 */}
      <section id="pending-tasks-section">
        <PendingTasksCard tasks={pendingTasks} />
      </section>

      {/* SECTION F: 系统概览 */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AccountOverviewCard
          activeProjects={stats.active_projects}
          activeAccounts={stats.active_accounts}
          totalBalance={stats.total_balance}
        />
        <SystemStatusCard />
      </section>
    </div>
  );
}

export default DashboardPage;
