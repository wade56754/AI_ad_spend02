/**
 * DashboardPage Component
 *
 * Main dashboard with metrics overview
 * Based on UI_DESIGN_SYSTEM.md v2.0
 *
 * Layout: PageHeader → StatCards → TrendCharts → BottomSection
 * Spacing: gap-6 (24px) for card grids, gap-8 (32px) for sections
 * Typography: H2 = text-2xl font-semibold
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import Link from 'next/link';
import {
  DollarSign,
  Users,
  BarChart3,
  Target,
  Plus,
  FileText,
  Wallet,
} from 'lucide-react';
import { useAuth } from '@/features/auth';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

import { DashboardHeader } from './DashboardHeader';
import { StatCard } from './StatCard';
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
import { AlertBanner, generateMockAlerts, type Alert } from './AlertBanner';
import {
  MainTrendChart,
  type MetricType,
  type TrendDataPoint as MainTrendDataPoint,
  generateSummary,
} from './MainTrendChart';
import { TopLists, generateMockTopLists } from './TopLists';

import type { PendingTask } from '../types';

// 根据日期预设获取天数
function getDaysFromPreset(preset: DateRangePreset): number {
  switch (preset) {
    case 'today': return 1;
    case '7d': return 7;
    case '30d': return 30;
    case 'custom': return 30; // 默认
    default: return 7;
  }
}

// 简单的伪随机数生成器（用于保证 SSR 和客户端一致性）
function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

// Generate mock trend data for main chart (multi-metric)
function generateMainTrendData(days: number): MainTrendDataPoint[] {
  const data: MainTrendDataPoint[] = [];
  const today = new Date();
  // 使用固定日期作为基准，确保每次生成相同
  today.setHours(0, 0, 0, 0);

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    const trendFactor = 1 + (days - i) * 0.002;
    // 使用日期索引作为种子，确保每次生成相同的"随机"值
    const seed = i * 12345;
    const randomFactor = (offset: number) => 1 + (seededRandom(seed + offset) - 0.5) * 0.15;

    const spend = Math.round(120000 * randomFactor(0) * trendFactor);
    const revenue = Math.round(160000 * randomFactor(1) * trendFactor);
    const profit = revenue - spend;
    const conversions = Math.round(3000 * randomFactor(2) * trendFactor);

    data.push({
      date: date.toISOString().split('T')[0],
      spend,
      revenue,
      profit,
      conversions,
    });
  }

  return data;
}

export function DashboardPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 全局日期范围状态
  const [globalDateRange, setGlobalDateRange] = useState<DateRangePreset>('7d');

  // 选中的指标状态 (用于 KPI 卡片联动主图)
  const [activeMetric, setActiveMetric] = useState<MetricType>('spend');

  // 告警列表 - 初始为空，避免 hydration 错误
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // 在客户端挂载后生成告警数据
  React.useEffect(() => {
    setAlerts(generateMockAlerts());
  }, []);

  // Helper function for currency formatting
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Mock data - TODO: Replace with actual API call using React Query
  // 按照 MASTER.md §6.5 核心页面最小字段集 (Phase 1)
  const stats = {
    // §6.5 必须字段 - 本月核心指标
    month_spend: 2856800.00,           // 本月总消耗 - ad_spend_daily SUM(spend)
    month_conversions: 72580,           // 本月总进粉 - daily_report SUM(conversions)
    overall_cpl: 39.36,                 // 整体 CPL - 总消耗/总进粉 (§4.5.2 规则)
    estimated_profit: 568000.00,        // 预计毛利 - §4.5.4 公式
    active_projects: 12,                // 活跃项目数 - project COUNT(status='active')
    abnormal_projects: 3,               // 异常项目数 - CPL > target × 1.3
    pending_topups: 3,                  // 待审批充值数 - topup_request COUNT(status='pending')
    // 今日视角 (辅助信息)
    today_spend: 125680.50,
    today_conversions: 3256,
    today_revenue: 162500.00,
    today_profit: 36819.50,
    // 变化率
    spend_change: 12.5,
    conversions_change: 8.3,
    cpl_change: -5.2,                   // CPL 下降是好事
    profit_change: 15.2,
    // 其他待处理
    pending_settlements: 2,
    pending_reconciliations: 5,
    pending_imports: 1,
    active_accounts: 45,
    total_balance: 856000.00,
    // CPL 目标
    cpl_target: 35.00,
  };

  // Mock trend data - 基于全局时间范围生成
  const mainTrendData = useMemo(
    () => generateMainTrendData(getDaysFromPreset(globalDateRange)),
    [globalDateRange]
  );

  // 生成自动总结
  const trendSummary = useMemo(
    () => generateSummary(mainTrendData, activeMetric),
    [mainTrendData, activeMetric]
  );

  // 计算 7 日均值 (用于 KPI 卡片)
  const average7d = useMemo(() => {
    const last7Days = mainTrendData.slice(-7);
    const avgSpend = last7Days.reduce((sum, d) => sum + (d.spend || 0), 0) / 7;
    const avgRevenue = last7Days.reduce((sum, d) => sum + (d.revenue || 0), 0) / 7;
    const avgProfit = last7Days.reduce((sum, d) => sum + (d.profit || 0), 0) / 7;
    const avgConversions = last7Days.reduce((sum, d) => sum + (d.conversions || 0), 0) / 7;

    return {
      spend: formatCurrency(avgSpend),
      revenue: formatCurrency(avgRevenue),
      profit: formatCurrency(avgProfit),
      conversions: Math.round(avgConversions).toLocaleString(),
    };
  }, [mainTrendData]);

  // Top lists data - Mock data for now
  const topListsData = useMemo(() => generateMockTopLists(), []);

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

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // TODO: Replace with actual API refresh call
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error('刷新数据失败:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Show skeleton loading state while auth is initializing
  if (isAuthLoading) {
    return (
      <div className="space-y-8" data-testid="dashboard-loading">
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
          onChange={(preset) => setGlobalDateRange(preset)}
        />
      </div>

      {/* Alert Banner - 风险告警条 */}
      {alerts.length > 0 && (
        <AlertBanner
          alerts={alerts}
          onDismiss={(id) => setAlerts(alerts.filter((a) => a.id !== id))}
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

      {/* §6.5 核心指标 - 本月概览 (MASTER.md 必须字段) */}
      <section>
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
            onClick={() => setActiveMetric('spend')}
            isActive={activeMetric === 'spend'}
            testId="dashboard-stat-card-spend"
          />
          <StatCard
            title="本月总进粉"
            value={stats.month_conversions.toLocaleString()}
            change={stats.conversions_change}
            average7d={average7d.conversions}
            target={`今日 ${stats.today_conversions.toLocaleString()}`}
            icon={<Users className="h-6 w-6" />}
            color="purple"
            onClick={() => setActiveMetric('conversions')}
            isActive={activeMetric === 'conversions'}
            testId="dashboard-stat-card-conversions"
          />
          <StatCard
            title="整体 CPL"
            value={`¥${stats.overall_cpl.toFixed(2)}`}
            change={stats.cpl_change}
            target={`目标 ¥${stats.cpl_target}`}
            icon={<BarChart3 className="h-6 w-6" />}
            color={stats.overall_cpl > stats.cpl_target * 1.3 ? 'red' : stats.overall_cpl > stats.cpl_target ? 'orange' : 'green'}
            testId="dashboard-stat-card-cpl"
          />
          <StatCard
            title="预计毛利"
            value={formatCurrency(stats.estimated_profit)}
            change={stats.profit_change}
            average7d={average7d.profit}
            target={`今日 ${formatCurrency(stats.today_profit)}`}
            icon={<Target className="h-6 w-6" />}
            color={stats.estimated_profit >= 0 ? 'green' : 'red'}
            onClick={() => setActiveMetric('profit')}
            isActive={activeMetric === 'profit'}
            testId="dashboard-stat-card-profit"
          />
        </div>
      </section>

      {/* §6.5 运营状态指标 */}
      <section>
        <h2 className="text-2xl font-semibold text-foreground mb-4">运营状态</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="活跃项目数"
            value={stats.active_projects.toString()}
            icon={<Target className="h-6 w-6" />}
            color="blue"
            testId="dashboard-stat-card-active-projects"
          />
          <StatCard
            title="异常项目数"
            value={stats.abnormal_projects.toString()}
            target="CPL 超标 30%+"
            icon={<BarChart3 className="h-6 w-6" />}
            color={stats.abnormal_projects > 0 ? 'red' : 'green'}
            testId="dashboard-stat-card-abnormal-projects"
          />
          <StatCard
            title="待审批充值"
            value={stats.pending_topups.toString()}
            target="需老板审批"
            icon={<Wallet className="h-6 w-6" />}
            color={stats.pending_topups > 0 ? 'orange' : 'green'}
            testId="dashboard-stat-card-pending-topups"
          />
        </div>
      </section>

      {/* Main Trend Chart - 主趋势图 */}
      <MainTrendChart
        data={mainTrendData}
        activeMetric={activeMetric}
        onMetricChange={setActiveMetric}
        summary={trendSummary}
      />

      {/* Top Lists - 归因列表 (新增) */}
      <TopLists
        topSpendCampaigns={topListsData.topSpend}
        worstROASCampaigns={topListsData.worstROAS}
      />

      {/* Pending Tasks Section - 待处理事项 */}
      <section id="pending-tasks-section">
        <PendingTasksCard tasks={pendingTasks} />
      </section>

      {/* Bottom Section - Account & System Info */}
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
