import { useState, useEffect } from 'react';

// 趋势数据类型定义
export interface TrendDataPoint {
  label: string;
  value: number;
}

export interface DashboardMetrics {
  totalSpend: string;
  totalTopup: string;
  activeAccounts: number;
  roi: string;
  spendChange: number;
  topupChange: number;
  accountsChange: number;
  roiChange: number;
}

export interface TodayMetrics {
  todaySpend: string;
  yesterdaySpend: string;
  weeklyAvg: string;
}

export interface AlertData {
  notifications: number;
  highRiskAlerts: number;
}

/**
 * Dashboard数据管理Hook
 * 按照UI设计规范要求，抽离mock数据到hooks层
 */
export function useDashboardData() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [todayMetrics, setTodayMetrics] = useState<TodayMetrics | null>(null);
  const [alerts, setAlerts] = useState<AlertData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 模拟数据加载
    const loadDashboardData = async () => {
      try {
        setLoading(true);

        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 500));

        // 设置指标数据
        setMetrics({
          totalSpend: "￥45,234",
          totalTopup: "￥128,500",
          activeAccounts: 156,
          roi: "3.24",
          spendChange: 12.5,
          topupChange: 8.2,
          accountsChange: 5,
          roiChange: 0.15
        });

        // 设置趋势数据
        setTrendData([
          { label: '周一', value: 85 },
          { label: '周二', value: 92 },
          { label: '周三', value: 78 },
          { label: '周四', value: 88 },
          { label: '周五', value: 95 },
          { label: '周六', value: 90 },
          { label: '周日', value: 82 }
        ]);

        // 设置今日指标
        setTodayMetrics({
          todaySpend: "￥2,850",
          yesterdaySpend: "￥3,120",
          weeklyAvg: "￥2,743"
        });

        // 设置告警数据
        setAlerts({
          notifications: 3,
          highRiskAlerts: 2
        });

        setError(null);
      } catch (err) {
        setError('加载Dashboard数据失败');
        console.error('Dashboard data loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // 重新加载数据的函数
  const refetch = () => {
    // 重置loading状态来触发重新加载
    setLoading(true);
    // 这里可以添加实际的重新加载逻辑
    setTimeout(() => {
      // 模拟重新加载完成
      setLoading(false);
    }, 500);
  };

  return {
    metrics,
    trendData,
    todayMetrics,
    alerts,
    loading,
    error,
    refetch
  };
}