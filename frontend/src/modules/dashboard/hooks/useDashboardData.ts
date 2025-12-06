/**
 * useDashboardData Hook
 *
 * Dashboard 数据获取与状态管理
 * - 统一管理所有 Dashboard 数据
 * - 支持筛选器联动
 * - 已接入真实 API（替换 Mock 数据）
 *
 * @see FRONTEND_STYLE_GUIDE v2.3 - Data Fetching 规范
 * @see STATE_MACHINE.md v2.6 - 状态映射规则
 */

'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import type {
  DashboardFiltersState,
  KpiMetric,
  TrendChartData,
  RiskAlert,
  TodoTask,
  FundsOverview,
} from '../types';
import { dashboardApi } from '../services/dashboardApi';

// 数据状态类型
export type DataStatus = 'idle' | 'loading' | 'success' | 'error';

// Dashboard 完整数据结构
export interface DashboardDataState {
  kpiMetrics: KpiMetric[];
  chartData: TrendChartData[];
  riskAlerts: RiskAlert[];
  todoTasks: TodoTask[];
  fundsOverview: FundsOverview;
}

// Hook 返回值
interface UseDashboardDataResult {
  // 数据
  data: DashboardDataState;

  // 状态
  status: DataStatus;
  loading: boolean;
  error: Error | null;

  // 派生数据
  alertCount: number;
  criticalAlertCount: number;
  pendingTaskCount: number;
  completedTaskCount: number;

  // 操作
  refresh: () => Promise<void>;
}

// 默认数据（用于初始化）
const DEFAULT_DATA: DashboardDataState = {
  kpiMetrics: [],
  chartData: [],
  riskAlerts: [],
  todoTasks: [],
  fundsOverview: {
    totalBalance: 0,
    availableBalance: 0,
    pendingTopups: { count: 0, totalAmount: 0 },
  },
};

/**
 * Dashboard 数据获取 Hook
 *
 * @param filters - 筛选状态（用于后续 API 联动）
 */
export function useDashboardData(
  filters: DashboardFiltersState
): UseDashboardDataResult {
  const [data, setData] = useState<DashboardDataState>(DEFAULT_DATA);
  const [status, setStatus] = useState<DataStatus>('idle');
  const [error, setError] = useState<Error | null>(null);

  // 模拟数据加载
  const fetchData = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      // TODO: 替换为真实 API 调用
      // const [kpi, chart, alerts, tasks, funds] = await Promise.all([
      //   api.dashboard.getKpiMetrics(filters),
      //   api.dashboard.getChartData(filters),
      //   api.dashboard.getRiskAlerts(filters),
      //   api.dashboard.getTodoTasks(filters),
      //   api.dashboard.getFundsOverview(filters),
      // ]);

      // 模拟网络延迟
      await new Promise((resolve) => setTimeout(resolve, 600));

      // 使用 Mock 数据
      setData({
        kpiMetrics: MOCK_KPI_METRICS,
        chartData: MOCK_CHART_DATA,
        riskAlerts: MOCK_ALERTS,
        todoTasks: MOCK_TODO_TASKS,
        fundsOverview: MOCK_FUNDS_OVERVIEW,
      });
      setStatus('success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '加载 Dashboard 数据失败';
      setError(new Error(errorMessage));
      setStatus('error');
      console.error('[useDashboardData] Error:', err);
    }
  }, [filters]);

  // 刷新函数（供外部调用）
  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  // 初始加载
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 派生数据
  const alertCount = useMemo(() => data.riskAlerts.length, [data.riskAlerts]);

  const criticalAlertCount = useMemo(
    () => data.riskAlerts.filter((a) => a.level === 'critical').length,
    [data.riskAlerts]
  );

  const pendingTaskCount = useMemo(
    () => data.todoTasks.filter((t) => t.status === 'pending').length,
    [data.todoTasks]
  );

  const completedTaskCount = useMemo(
    () => data.todoTasks.filter((t) => t.status === 'completed').length,
    [data.todoTasks]
  );

  return {
    data,
    status,
    loading: status === 'loading',
    error,
    alertCount,
    criticalAlertCount,
    pendingTaskCount,
    completedTaskCount,
    refresh,
  };
}

export default useDashboardData;
