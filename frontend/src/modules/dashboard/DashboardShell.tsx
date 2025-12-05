/**
 * DashboardShell - Dashboard 模块级 Shell 组件
 *
 * 职责：
 * - 整合 Dashboard 所有数据 hooks 和 UI 组件
 * - 处理页面级事件（路由跳转等）
 * - 提供可复用的仪表盘模板
 *
 * 布局结构（12 栅格）：
 * - Header: 标题 + 筛选器 + 快捷操作
 * - KPI 区: Primary (4+4) + Secondary (2+2) = 12 栅格
 * - 中段: 趋势图 (8 栅格) + 风险预警 (4 栅格) = 12 栅格
 * - 底部: 今日待办 (8 栅格) + 资金概览 (4 栅格) = 12 栅格
 *
 * @see FRONTEND_STYLE_GUIDE v2.3 - Shell 组件规范
 */

'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DataStateManager } from '@/components/ui/data-state/DataStateManager';
import {
  DashboardHeader,
  DashboardKpiRow,
  DashboardTrendSection,
  DashboardRiskPanel,
  DashboardTodayTasks,
  DashboardFundsOverview,
} from './components';
import { useDashboardFilters, useDashboardData } from './hooks';
import type { RiskAlert, TodoTask } from './types';

export interface DashboardShellProps {
  /** 自定义 className */
  className?: string;
}

/**
 * Dashboard Shell 组件
 *
 * 使用示例：
 * ```tsx
 * <PageContainer>
 *   <DashboardShell />
 * </PageContainer>
 * ```
 */
export function DashboardShell({ className }: DashboardShellProps) {
  const router = useRouter();

  // 筛选状态管理
  const {
    filters,
    projectOptions,
    setDateRange,
    setProjectId,
    dateRangeLabel,
    projectLabel,
  } = useDashboardFilters();

  // 数据获取
  const {
    data,
    loading,
    error,
    alertCount,
    refresh,
  } = useDashboardData(filters);

  // ============================================================================
  // 事件处理函数
  // ============================================================================

  const handleViewAllAlerts = () => {
    router.push('/dashboard/risk-alerts');
  };

  const handleAlertClick = (alert: RiskAlert) => {
    router.push(`/dashboard/ad-accounts/${alert.account}`);
  };

  const handleTaskClick = (task: TodoTask) => {
    if (task.relatedEntityType && task.relatedEntityId) {
      const routes: Record<string, string> = {
        daily_report: `/dashboard/daily-reports/${task.relatedEntityId}`,
        topup_request: `/dashboard/topups/${task.relatedEntityId}`,
        reconciliation: `/dashboard/reconciliation/${task.relatedEntityId}`,
      };
      router.push(routes[task.relatedEntityType] || '/dashboard');
    }
  };

  const handleTaskHandle = (task: TodoTask) => {
    handleTaskClick(task);
  };

  const handleTopupClick = () => {
    router.push('/dashboard/topups');
  };

  // ============================================================================
  // 加载状态
  // ============================================================================

  if (loading && !data.kpiMetrics.length) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-text-muted">
        <Loader2 className="w-8 h-8 animate-spin mr-2" />
        正在加载全景数据...
      </div>
    );
  }

  // ============================================================================
  // 错误状态
  // ============================================================================

  if (error && !data.kpiMetrics.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-text-muted">
        <p className="text-danger mb-4">{error.message}</p>
        <Button
          onClick={refresh}
          className="bg-accent text-white hover:bg-accent-dark"
        >
          重新加载
        </Button>
      </div>
    );
  }

  // ============================================================================
  // 主渲染
  // ============================================================================

  return (
    <div className={className}>
      <div className="flex flex-col gap-6 w-full py-6">
        {/* Header: 标题 + 筛选器 + 快捷操作 */}
        <DashboardHeader
          filters={filters}
          dateRangeLabel={dateRangeLabel}
          projectLabel={projectLabel}
          projectOptions={projectOptions}
          alertCount={alertCount}
          loading={loading}
          onDateRangeChange={setDateRange}
          onProjectChange={setProjectId}
          onRefresh={refresh}
        />

        {/* KPI 指标卡片区 - 12 栅格布局 */}
        <DashboardKpiRow metrics={data.kpiMetrics} />

        {/* 中段核心区：图表 (8 栅格) + 预警 (4 栅格) */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-12 lg:col-span-8">
            <DashboardTrendSection data={data.chartData} />
          </div>
          <div className="col-span-12 lg:col-span-4">
            <DashboardRiskPanel
              alerts={data.riskAlerts}
              onViewAll={handleViewAllAlerts}
              onAlertClick={handleAlertClick}
            />
          </div>
        </div>

        {/* 底部区域：今日待办 (8 栅格) + 资金概览 (4 栅格) */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-12 lg:col-span-8">
            <DataStateManager
              status={loading ? 'loading' : error ? 'error' : 'success'}
              data={data.todoTasks}
              isEmpty={(tasks) => !tasks || tasks.length === 0}
              loadingType="skeleton"
              emptyType="no-data"
            >
              {(tasks) => (
                <DashboardTodayTasks
                  tasks={tasks}
                  onTaskClick={handleTaskClick}
                  onHandleTask={handleTaskHandle}
                />
              )}
            </DataStateManager>
          </div>
          <div className="col-span-12 lg:col-span-4">
            <DashboardFundsOverview
              data={data.fundsOverview}
              onTopupClick={handleTopupClick}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardShell;
