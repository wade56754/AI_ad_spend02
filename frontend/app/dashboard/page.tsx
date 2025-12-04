'use client';

import React, { useState, useEffect, useCallback } from 'react';
import PageContainer from '@/components/layout/page-container';
import {
  DashboardFilters,
  KpiCards,
  TrendSection,
  TodayTasksCard,
} from '@/modules/dashboard';
import {
  mockProjects,
  mockKpiMetrics,
  mockSpendTrend,
  mockRoiTrend,
  mockTodoTasks,
} from '@/modules/dashboard/data/mock-data';
import type { DashboardFilters as FilterState } from '@/modules/dashboard/types';

export default function DashboardPage() {
  // 筛选器状态
  const [filters, setFilters] = useState<FilterState>({
    dateRange: '7d',
    projectId: undefined,
  });

  // 数据加载状态
  const [loading, setLoading] = useState(true);

  // 模拟数据加载
  const loadData = useCallback(async () => {
    setLoading(true);
    // 模拟 API 延迟
    await new Promise(resolve => setTimeout(resolve, 800));
    setLoading(false);
  }, []);

  // 初始加载
  useEffect(() => {
    loadData();
  }, [loadData]);

  // 筛选器变化时重新加载
  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
    loadData();
  };

  // 刷新数据
  const handleRefresh = () => {
    loadData();
  };

  return (
    <PageContainer>
      <div className="flex flex-col gap-6 w-full">
        {/* 页面标题 */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">概览</h1>
          <p className="text-muted-foreground">
            欢迎使用 AI广告代投系统管理后台
          </p>
        </div>

        {/* 顶部筛选器 */}
        <DashboardFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          projects={mockProjects}
          onRefresh={handleRefresh}
          loading={loading}
        />

        {/* KPI 指标卡片 */}
        <KpiCards
          metrics={mockKpiMetrics}
          loading={loading}
        />

        {/* 趋势图表区 */}
        <TrendSection
          spendTrend={mockSpendTrend}
          roiTrend={mockRoiTrend}
          loading={loading}
        />

        {/* 底部区域：待办列表 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TodayTasksCard
            title="今日待办"
            tasks={mockTodoTasks}
          />
          {/* 预留右侧区域，可放置其他卡片如异常账户、快速入口等 */}
          <div className="rounded-2xl border border-dashed border-slate-200 p-6 flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              更多功能模块占位（如异常账户、快速入口）
            </p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
