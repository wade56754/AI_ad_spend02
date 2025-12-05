/**
 * useFinanceData - 财务模块数据获取
 *
 * TODO: 接入真实 API 后替换 mock 数据
 *
 * 对齐：FRONTEND_STYLE_GUIDE v2.3, FRONTEND_MODULE_SHELL_PATTERN v1.0
 */

'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import type {
  FinanceFiltersState,
  FinanceDataState,
  TopupRequest,
} from '../types';
import {
  MOCK_TOPUP_REQUESTS,
  MOCK_FINANCIAL_SUMMARY,
  MOCK_SPENDING_TRENDS,
  MOCK_PLATFORM_SPENDING,
  MOCK_TEAM_SPENDING,
} from '../data/mock-data';

export type DataStatus = 'idle' | 'loading' | 'success' | 'error';

const DEFAULT_DATA: FinanceDataState = {
  topupRequests: [],
  financialSummary: MOCK_FINANCIAL_SUMMARY,
  spendingTrends: [],
  platformSpending: [],
  teamSpending: [],
};

export function useFinanceData(filters: FinanceFiltersState) {
  const [data, setData] = useState<FinanceDataState>(DEFAULT_DATA);
  const [status, setStatus] = useState<DataStatus>('idle');
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setStatus('loading');
    setError(null);

    try {
      // TODO: 替换为真实 API 调用
      // const response = await apiFetch('/api/finance/dashboard');
      await new Promise((resolve) => setTimeout(resolve, 800));

      setData({
        topupRequests: MOCK_TOPUP_REQUESTS,
        financialSummary: MOCK_FINANCIAL_SUMMARY,
        spendingTrends: MOCK_SPENDING_TRENDS,
        platformSpending: MOCK_PLATFORM_SPENDING,
        teamSpending: MOCK_TEAM_SPENDING,
      });
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err : new Error('加载财务数据失败'));
      setStatus('error');
    }
  }, []);

  const refresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 筛选后的充值申请列表
  const filteredTopupRequests = useMemo(() => {
    return data.topupRequests.filter((request) => {
      const matchesSearch =
        request.user_name.toLowerCase().includes(filters.search.toLowerCase()) ||
        request.account_name.toLowerCase().includes(filters.search.toLowerCase()) ||
        request.reason.toLowerCase().includes(filters.search.toLowerCase());
      const matchesStatus =
        filters.status === 'all' || request.status === filters.status;
      return matchesSearch && matchesStatus;
    });
  }, [data.topupRequests, filters.search, filters.status]);

  // 待审核数量
  const pendingCount = useMemo(() => {
    return data.topupRequests.filter((r) => r.status === 'pending').length;
  }, [data.topupRequests]);

  // 审批充值申请
  const approveRequest = useCallback((requestId: number, comment: string) => {
    setData((prev) => ({
      ...prev,
      topupRequests: prev.topupRequests.map((req) =>
        req.id === requestId
          ? {
              ...req,
              status: 'approved' as const,
              reviewed_at: new Date().toISOString(),
              reviewed_by: '当前用户',
              review_comment: comment || '批准充值申请',
            }
          : req
      ),
    }));
  }, []);

  // 拒绝充值申请
  const rejectRequest = useCallback((requestId: number, comment: string) => {
    setData((prev) => ({
      ...prev,
      topupRequests: prev.topupRequests.map((req) =>
        req.id === requestId
          ? {
              ...req,
              status: 'rejected' as const,
              reviewed_at: new Date().toISOString(),
              reviewed_by: '当前用户',
              review_comment: comment || '申请被拒绝',
            }
          : req
      ),
    }));
  }, []);

  // 标记为完成
  const completeRequest = useCallback((requestId: number) => {
    setData((prev) => ({
      ...prev,
      topupRequests: prev.topupRequests.map((req) =>
        req.id === requestId
          ? {
              ...req,
              status: 'completed' as const,
              completed_at: new Date().toISOString(),
            }
          : req
      ),
    }));
  }, []);

  return {
    data,
    filteredTopupRequests,
    pendingCount,
    status,
    loading: status === 'loading',
    error,
    refresh,
    approveRequest,
    rejectRequest,
    completeRequest,
  };
}
