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
import {
  DollarSign,
  Users,
  BarChart3,
  Target,
} from 'lucide-react';
import { useAuth } from '@/modules/auth';
import { Skeleton } from '@/components/ui/skeleton';

import { DashboardHeader } from './DashboardHeader';
import { TrendChart, type TimeRange } from './charts';
import { StatCard } from './StatCard';
import { PendingTasksCard } from './PendingTasksCard';
import { QuickActionsCard } from './QuickActionsCard';
import { AccountOverviewCard } from './AccountOverviewCard';
import { SystemStatusCard } from './SystemStatusCard';
import {
  StatCardSkeleton,
  TrendChartSkeleton,
  CardSkeleton,
} from './StatCardSkeleton';

import { QUICK_ACTIONS } from '../types';
import type { PendingTask, TrendDataPoint } from '../types';

// 时间范围标签映射
const TIME_RANGE_LABELS: Record<TimeRange, string> = {
  '7d': '近7日',
  '30d': '近30日',
  '90d': '近90日',
};

// 根据时间范围获取天数
function getDaysFromRange(range: TimeRange): number {
  switch (range) {
    case '7d': return 7;
    case '30d': return 30;
    case '90d': return 90;
    default: return 7;
  }
}

// Generate mock trend data for specified days
function generateTrendData(baseValue: number, days: number, variance: number = 0.2): TrendDataPoint[] {
  const data: TrendDataPoint[] = [];
  const today = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    // 添加一些趋势变化，让数据更真实
    const trendFactor = 1 + (days - i) * 0.002; // 轻微上升趋势
    const randomFactor = 1 + (Math.random() - 0.5) * variance;
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(baseValue * randomFactor * trendFactor),
    });
  }

  return data;
}

export function DashboardPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 每个图表的时间范围状态
  const [spendTimeRange, setSpendTimeRange] = useState<TimeRange>('7d');
  const [conversionsTimeRange, setConversionsTimeRange] = useState<TimeRange>('7d');
  const [revenueTimeRange, setRevenueTimeRange] = useState<TimeRange>('7d');

  // Mock data - TODO: Replace with actual API call using React Query
  const stats = {
    today_spend: 125680.50,
    today_conversions: 3256,
    today_revenue: 162500.00,
    today_profit: 36819.50,
    spend_change: 12.5,
    conversions_change: 8.3,
    revenue_change: 10.8,
    profit_change: 15.2,
    pending_topups: 3,
    pending_settlements: 2,
    pending_reconciliations: 5,
    pending_imports: 1,
    active_projects: 12,
    active_accounts: 45,
    total_balance: 856000.00,
  };

  // Mock trend data - 基于所选时间范围动态生成
  const spendTrendData = useMemo(
    () => generateTrendData(120000, getDaysFromRange(spendTimeRange), 0.15),
    [spendTimeRange]
  );
  const conversionsTrendData = useMemo(
    () => generateTrendData(3000, getDaysFromRange(conversionsTimeRange), 0.2),
    [conversionsTimeRange]
  );
  const revenueTrendData = useMemo(
    () => generateTrendData(160000, getDaysFromRange(revenueTimeRange), 0.18),
    [revenueTimeRange]
  );

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

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

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
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Page Header */}
      <DashboardHeader
        userName={user?.full_name || user?.username || '用户'}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
      />

      {/* Today's Stats - 4 columns */}
      <section>
        <h2 className="text-2xl font-semibold text-foreground mb-4">今日概览</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="今日消耗"
            value={formatCurrency(stats.today_spend)}
            change={stats.spend_change}
            icon={<DollarSign className="h-6 w-6" />}
            color="blue"
            href="/ad-spend"
            testId="dashboard-stat-card-spend"
          />
          <StatCard
            title="今日粉数"
            value={stats.today_conversions.toLocaleString()}
            change={stats.conversions_change}
            icon={<Users className="h-6 w-6" />}
            color="purple"
            href="/daily-reports"
            testId="dashboard-stat-card-conversions"
          />
          <StatCard
            title="今日收入"
            value={formatCurrency(stats.today_revenue)}
            change={stats.revenue_change}
            icon={<BarChart3 className="h-6 w-6" />}
            color="green"
            href="/finance/profit"
            testId="dashboard-stat-card-revenue"
          />
          <StatCard
            title="今日利润"
            value={formatCurrency(stats.today_profit)}
            change={stats.profit_change}
            icon={<Target className="h-6 w-6" />}
            color="orange"
            href="/finance/profit"
            testId="dashboard-stat-card-profit"
          />
        </div>
      </section>

      {/* Trend Section */}
      <section>
        <h2 className="text-2xl font-semibold text-foreground mb-4">数据趋势</h2>
        {/* Row 1: Two charts side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <TrendChart
            title="消耗趋势"
            description="每日广告消耗金额变化"
            data={spendTrendData}
            height={260}
            showTimeRangeSelector={true}
            defaultTimeRange={spendTimeRange}
            onTimeRangeChange={setSpendTimeRange}
            color="blue"
            testId="dashboard-chart-spend"
          />
          <TrendChart
            title="粉数趋势"
            description="每日进粉数量变化"
            data={conversionsTrendData}
            height={260}
            showTimeRangeSelector={true}
            defaultTimeRange={conversionsTimeRange}
            onTimeRangeChange={setConversionsTimeRange}
            color="violet"
            testId="dashboard-chart-conversions"
          />
        </div>
        {/* Row 2: Full width chart */}
        <TrendChart
          title="收入趋势"
          description="每日收入金额变化"
          data={revenueTrendData}
          height={280}
          showTimeRangeSelector={true}
          defaultTimeRange={revenueTimeRange}
          onTimeRangeChange={setRevenueTimeRange}
          color="green"
          testId="dashboard-chart-revenue"
        />
      </section>

      {/* Bottom Section */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - 2/3 width */}
        <div className="lg:col-span-2 space-y-6">
          <PendingTasksCard tasks={pendingTasks} />
          <QuickActionsCard actions={QUICK_ACTIONS} />
        </div>

        {/* Right Column - 1/3 width */}
        <div className="space-y-6">
          <AccountOverviewCard
            activeProjects={stats.active_projects}
            activeAccounts={stats.active_accounts}
            totalBalance={stats.total_balance}
          />
          <SystemStatusCard />
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;
